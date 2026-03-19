from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required 

from .models import User, Listing, Bid, Comment


def index(request):
    active_listing = Listing.objects.filter(active=True)
    return render(request, "auctions/index.html",{
        "listings": active_listing
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required
def create_listing(request):
    if request.method == "POST":
        title = request.POST["title"]
        description = request.POST["description"]
        starting_bid = request.POST["starting_bid"]
        image_url = request.POST["image_url"]
        category = request.POST["category"]

        listing = Listing(
            owner=request.user,
            title=title,
            description=description,
            starting_bid=starting_bid,
            image_url=image_url,
            category=category
        )
        listing.save()
        return redirect("index")
    return render (request, "auctions/create_listing.html")

def listing_detail(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    bids = Bid.objects.filter(listing=listing).order_by("-amount")
    highest_bid = bids.first() if bids.exists() else None 
    winner = highest_bid.user if highest_bid else None
    if bids.exists():
            current_price = bids.first().amount
    else:
            current_price = listing.starting_bid
    bid_count = Bid.objects.filter(listing=listing).count()
    comments = Comment.objects.filter(listing=listing).order_by("-created_at")
    if request.method == "POST":
        if "bid_submit" in request.POST:
            bid_amount = float(request.POST["bid_amount"])
            if bid_amount > current_price:
                Bid.objects.create(
                    user=request.user,
                    listing=listing,
                    amount=bid_amount
                )
                return redirect("listing_detail", listing_id=listing.id)   
            else:
                return render(request, "auctions/listing_detail.html", {
                    "listing": listing,
                    "current_price": current_price,
                    "bid_count": bid_count,
                    "comments": comments,
                    "error": "Bid must be higher than current price.",
                    "winner": winner
                })
            
        elif "comment_submit" in request.POST:
            content = request.POST["comment_content"]
            Comment.objects.create(
                user=request.user,
                listing=listing,
                content=content
            )
            return redirect("listing_detail", listing_id=listing.id)
    highest_bid = bids.first
    return render(request, "auctions/listing_detail.html", {
        "listing": listing,
        "current_price": current_price,
        "bid_count": bid_count,
        "comments": comments,
        "winner": winner 
    })

@login_required
def watchlist(request):
    listings = request.user.watchlist.all()
    return render(request, "auctions/watchlist.html", {
        "listings": listings
    })

@login_required 
def toggle_watchlist(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)

    if request.user in listing.watchers.all():
        listing.watchers.remove(request.user)
    else:
        listing.watchers.add(request.user)
    return redirect("listing_detail", listing_id = listing.id)

def categories(request):
    categories = Listing.objects.filter(active=True).exclude(category="").values_list("category", flat=True).distinct()

    return render(request, "auctions/categories.html", {
        "categories": categories
    })

def category_listings(request, category_name):
    listings = Listing.objects.filter(active=True, category=category_name)
    
    return render(request, "auctions/category_listings.html", {
        "category_name": category_name,
        "listings": listings
    })

@login_required
def close_auction(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)

    if request.user != listing.owner :
        return redirect("listing_detail", listing_id=listing.id)
    
    if request.method == "POST":
        listing.active = False
        listing.save()
    
    return redirect("listing_detail", listing_id = listing.id)
