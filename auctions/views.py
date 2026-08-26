from decimal import Decimal, InvalidOperation

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404

from .models import User, Listing, Bid, Comment


def index(request):
    return render(request, "auctions/index.html", {
        "listings": Listing.objects.filter(active=True)
    })


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("index")

        return render(request, "auctions/login.html", {
            "message": "Invalid username and/or password."
        })

    return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return redirect("index")


def register(request):
    if request.method == "POST":
        username = request.POST.get("username", "")
        email = request.POST.get("email", "")
        password = request.POST.get("password", "")
        confirmation = request.POST.get("confirmation", "")

        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        try:
            user = User.objects.create_user(username, email, password)
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })

        login(request, user)
        return redirect("index")

    return render(request, "auctions/register.html")


@login_required
def create_listing(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()

        try:
            starting_bid = Decimal(request.POST.get("starting_bid", ""))
        except InvalidOperation:
            return render(request, "auctions/create_listing.html", {
                "error": "The starting bid has to be a number."
            })

        if not title or starting_bid <= 0:
            return render(request, "auctions/create_listing.html", {
                "error": "Please enter a title and a starting bid above 0."
            })

        listing = Listing.objects.create(
            owner=request.user,
            title=title,
            description=request.POST.get("description", "").strip(),
            starting_bid=starting_bid,
            image_url=request.POST.get("image_url", "").strip(),
            category=request.POST.get("category", "").strip(),
        )
        return redirect("listing_detail", listing_id=listing.id)

    return render(request, "auctions/create_listing.html")


def listing_detail(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    bids = Bid.objects.filter(listing=listing).order_by("-amount")
    highest_bid = bids.first()

    if highest_bid:
        current_price = highest_bid.amount
    else:
        current_price = listing.starting_bid

    # there is only a winner once the auction is closed
    if highest_bid and not listing.active:
        winner = highest_bid.user
    else:
        winner = None

    context = {
        "listing": listing,
        "current_price": current_price,
        "bid_count": bids.count(),
        "comments": Comment.objects.filter(listing=listing).order_by("-created_at"),
        "winner": winner,
    }

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect("login")

        if "bid_submit" in request.POST:
            if not listing.active:
                context["error"] = "This auction is already closed."
                return render(request, "auctions/listing_detail.html", context)

            try:
                bid_amount = Decimal(request.POST.get("bid_amount", ""))
            except InvalidOperation:
                context["error"] = "Please enter a number."
                return render(request, "auctions/listing_detail.html", context)

            if bid_amount <= current_price:
                context["error"] = "Bid must be higher than current price."
                return render(request, "auctions/listing_detail.html", context)

            Bid.objects.create(user=request.user, listing=listing, amount=bid_amount)
            return redirect("listing_detail", listing_id=listing.id)

        if "comment_submit" in request.POST:
            content = request.POST.get("comment_content", "").strip()

            if not content:
                context["error"] = "The comment is empty."
                return render(request, "auctions/listing_detail.html", context)

            Comment.objects.create(user=request.user, listing=listing, content=content)
            return redirect("listing_detail", listing_id=listing.id)

    return render(request, "auctions/listing_detail.html", context)


@login_required
def watchlist(request):
    return render(request, "auctions/watchlist.html", {
        "listings": request.user.watchlist.all()
    })


@login_required
def toggle_watchlist(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)

    if request.user in listing.watchers.all():
        listing.watchers.remove(request.user)
    else:
        listing.watchers.add(request.user)

    return redirect("listing_detail", listing_id=listing.id)


def categories(request):
    names = (Listing.objects
             .filter(active=True)
             .exclude(category="")
             .values_list("category", flat=True)
             .distinct())

    return render(request, "auctions/categories.html", {
        "categories": names
    })


def category_listings(request, category_name):
    return render(request, "auctions/category_listings.html", {
        "category_name": category_name,
        "listings": Listing.objects.filter(active=True, category=category_name)
    })


@login_required
def close_auction(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)

    if request.method == "POST" and request.user == listing.owner:
        listing.active = False
        listing.save()

    return redirect("listing_detail", listing_id=listing.id)
