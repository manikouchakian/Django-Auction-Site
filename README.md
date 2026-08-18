# Django Auction Site

A small auction platform built with Django. Users can create listings, place bids,
comment, and keep a watchlist.

I built this for CS50 Web. I kept working on it after the assignment was done,
because I wanted to understand the bidding logic and not just pass the check.

## Features

- Create and close auction listings
- Place bids; a bid is only accepted if it beats the current price
- One comment thread per listing
- Watchlist per user
- Categories with a listing overview
- Login, register, logout with Django's auth system

## Stack

Python · Django · SQLite

## Run it

    python -m venv .venv
    source .venv/bin/activate
    pip install django
    python manage.py migrate
    python manage.py runserver

## Configuration

Two settings come from the environment:

    export DJANGO_SECRET_KEY="your-own-random-key"
    export DJANGO_DEBUG=0

If you do not set them, the project falls back to a public development key and
`DEBUG=1`. That is fine on your own machine and wrong everywhere else.

An earlier version of this repository had the key written directly in
`commerce/settings.py`, and it is still in the git history. I do not use that key
any more. It only ever protected a local SQLite file.

## State

Works end to end.

## License

MIT
