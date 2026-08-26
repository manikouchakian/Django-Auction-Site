from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Bid, Comment, Listing

User = get_user_model()


class ListingTestCase(TestCase):
    """Tests for bidding, the watchlist and closing an auction."""

    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pw-owner")
        self.bidder = User.objects.create_user(username="bidder", password="pw-bidder")
        self.listing = Listing.objects.create(
            owner=self.owner,
            title="Old bicycle",
            description="Rides fine.",
            starting_bid=Decimal("10.00"),
            category="Sport",
        )
        self.url = reverse("listing_detail", args=[self.listing.id])

    def bid(self, amount):
        return self.client.post(self.url, {"bid_submit": "1", "bid_amount": amount})

    def test_starting_bid_is_the_first_current_price(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context["current_price"], Decimal("10.00"))
        self.assertEqual(response.context["bid_count"], 0)

    def test_bid_above_the_current_price_is_accepted(self):
        self.client.login(username="bidder", password="pw-bidder")
        response = self.bid("15.00")

        self.assertRedirects(response, self.url)
        self.assertEqual(Bid.objects.count(), 1)
        self.assertEqual(self.client.get(self.url).context["current_price"], Decimal("15.00"))

    def test_bid_equal_to_the_current_price_is_rejected(self):
        self.client.login(username="bidder", password="pw-bidder")
        response = self.bid("10.00")

        self.assertEqual(Bid.objects.count(), 0)
        self.assertIn("error", response.context)

    def test_bid_below_the_current_price_is_rejected(self):
        self.client.login(username="bidder", password="pw-bidder")
        self.bid("15.00")
        response = self.bid("12.00")

        self.assertEqual(Bid.objects.count(), 1)
        self.assertIn("error", response.context)

    def test_owner_can_close_the_auction(self):
        self.client.login(username="owner", password="pw-owner")
        self.client.post(reverse("close_auction", args=[self.listing.id]))

        self.listing.refresh_from_db()
        self.assertFalse(self.listing.active)

    def test_a_stranger_cannot_close_the_auction(self):
        self.client.login(username="bidder", password="pw-bidder")
        self.client.post(reverse("close_auction", args=[self.listing.id]))

        self.listing.refresh_from_db()
        self.assertTrue(self.listing.active)

    def test_watchlist_toggles_on_and_off(self):
        self.client.login(username="bidder", password="pw-bidder")
        watch_url = reverse("toggle_watchlist", args=[self.listing.id])

        self.client.post(watch_url)
        self.assertIn(self.listing, self.bidder.watchlist.all())

        self.client.post(watch_url)
        self.assertNotIn(self.listing, self.bidder.watchlist.all())

    def test_watchlist_requires_a_login(self):
        response = self.client.get(reverse("watchlist"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_a_comment_is_attached_to_the_listing(self):
        self.client.login(username="bidder", password="pw-bidder")
        self.client.post(self.url, {"comment_submit": "1", "comment_content": "Still available?"})

        comment = Comment.objects.get()
        self.assertEqual(comment.listing, self.listing)
        self.assertEqual(comment.user, self.bidder)
