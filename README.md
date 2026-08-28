# Django Auction Site

![tests](https://github.com/manikouchakian/Django-Auction-Site/actions/workflows/tests.yml/badge.svg)

A small auction platform built with Django. Users can create listings, place
bids, comment and keep a watchlist.

I built this for CS50 Web. After the assignment was done I kept working on it,
because I wanted the bidding to actually be correct and not just pass the
check.

## Features

- Create and close auction listings
- Place bids, a bid is only accepted if it beats the current price
- One comment thread per listing
- Watchlist per user
- Categories with a listing overview
- Login, register and logout with Django's auth system

## Stack

Python · Django · SQLite · Bootstrap

## Run it

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver

For anything but local development, set these two:

    DJANGO_SECRET_KEY=your-own-key
    DJANGO_DEBUG=0

Without them the project falls back to a development key and `DEBUG=True`.
That is fine on my own machine and nowhere else.

## Tests

    python manage.py test

13 tests for bidding, the watchlist, closing an auction and the error cases.
They also run on every push, see the badge above.

## Things I fixed after the assignment

**Bids were parsed with `float`.** `Bid.amount` is a `DecimalField`, so a float
loses precision on the way in. Money and floating point do not go together,
`0.1 + 0.2` is not `0.3`.

**A bid that was not a number crashed the page.** `float("abc")` throws and
nothing caught it, so the server answered with a 500 instead of a message.

**You could still bid on a closed auction.** Nothing checked `listing.active`
before saving the bid.

**Not logged in and still posting.** The detail view had no login check, so an
anonymous POST ran into an error deep inside Django instead of a redirect.

**The winner was shown while the auction was still running.** There is only a
winner once the auction is closed.

**`bids.first` without the brackets.** That stores the method itself instead of
calling it. Python says nothing, it just quietly does the wrong thing.

**`LOGIN_URL` was never set.** Django then sends everyone to
`/accounts/login/`, and that URL does not exist here, so `@login_required`
ended in a 404. My test for it passed anyway, because `/login` happens to be a
substring of `/accounts/login/`. A green test does not mean a working page.

**A `</form>` outside its `{% if %}`.** Visitors who were not logged in got a
closing tag without an opening one.

## Next steps

- Django Forms instead of reading `request.POST` by hand, that would move the
  validation out of the view
- A real end time for an auction instead of closing it manually
- PostgreSQL instead of SQLite

## License

MIT
