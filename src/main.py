from datetime import datetime, timedelta, timezone
from flask import abort, Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from . import db
from . import models
from .models import Card
from .models import Deck

main = Blueprint('main', __name__)

#
# redirect to the decks list
#
@main.route('/')
@login_required
def index():
    return redirect(url_for('main.decks'))

#
# show the decks list page
#
@main.route('/decks')
@login_required
def decks():
    decks = db.session.execute(db.select(Deck).filter_by(owner=current_user.id).order_by(Deck.name)).scalars().all()
    return render_template('decks.html', decks=decks)

#
# show the current due card for a deck
# 
# only the front of the card is shown unless the request includes a 'back' key in its query string
#
@main.route('/decks/<int:deck_id>')
@login_required
def deck(deck_id):
    # ensure the current user owns this deck
    owner = current_user.id
    deck = db.session.execute(db.select(Deck).filter_by(id=deck_id,owner=owner)).scalar()
    if not deck:
        abort(404)

    now = datetime.now(timezone.utc)
    card_query = db.select(Card).filter(Card.deck_id == deck_id, Card.due <= now).order_by(Card.due, Card.id)

    card = db.session.execute(card_query).scalar()

    if request.args.get('back'):
        side = 'back'
    else:
        side = 'front'

    return render_template('deck.html', deck=deck, card=card, side=side)

#
# this route handles processing the "remembered" and "forgot" buttons for a card
#
@main.route('/decks/<int:deck_id>/cards/<int:card_id>', methods=['POST'])
@login_required
def card_post(deck_id, card_id):
    # ensure the deck is owned by the current user
    owner = current_user.id
    deck = db.session.execute(db.select(Deck).filter_by(id=deck_id,owner=owner)).scalar()
    if not deck:
        abort(404)

    # find the card to update
    card = db.session.execute(db.select(Card).filter_by(id=card_id, deck_id=deck_id)).scalar()
    if not card:
        abort(404)

    command = request.form['command']
    now = datetime.now(timezone.utc)

    # if the user remembered the card, then increase the time interval until it is due again
    if command == 'remembered':
        due = card.due
        interval = card.interval
        card.interval = interval + 1
        # the amount of time to add depends on how many consecutive times the user
        # remembered the card. TODO configure these values better?
        match interval:
            case 0:
                card.due = due + timedelta(hours=2)
            case 1:
                card.due = due + timedelta(hours=4)
            case 2:
                card.due = due + timedelta(hours=8)
            case 3:
                card.due = due + timedelta(hours=16)
            case 4:
                card.due = due + timedelta(hours=32)
            case 5:
                card.due = due + timedelta(hours=64)
            case 6:
                card.due = due + timedelta(hours=128)
            case 7:
                card.due = due + timedelta(hours=256)
            case 8:
                card.due = due + timedelta(hours=512)
            case _:
                card.due = due + timedelta(hours=1024)

    # if the user forgot the card, then make it due again very soon
    if command == 'forgot':
        card.due = now + timedelta(minutes=1)
        card.interval = 0

    card.last_seen = now
    db.session.commit()

    return redirect(url_for('main.deck', deck_id=deck_id))

#
# shows the new-card page
#
@main.route('/decks/<int:deck_id>/new-card')
@login_required
def new_card(deck_id):
    owner = current_user.id
    deck = db.session.execute(db.select(Deck).filter_by(id=deck_id,owner=owner)).scalar()
    if not deck:
        abort(404)

    return render_template('new-card.html', deck=deck)

#
# creates a new card via the form on the new-card page
#
@main.route('/decks/<int:deck_id>/new-card', methods=['POST'])
@login_required
def new_card_post(deck_id):
    # ensure that the current user owns this deck
    owner = current_user.id
    deck = db.session.execute(db.select(Deck).filter_by(id=deck_id,owner=owner)).scalar()
    if not deck:
        abort(404)

    # create the new card
    front = request.form['front']
    back = request.form['back']
    now = datetime.now(timezone.utc)
    card = Card(deck_id=deck_id, front=front, back=back, interval=0, due=now)
    db.session.add(card)
    db.session.commit()

    return redirect(url_for('main.deck', deck_id=deck_id))

#
# shows the new-deck page
#
@main.route('/new-deck')
@login_required
def new_deck():
    return render_template('new-deck.html')

#
# craetes a new deck via the form on the new deck page
#
@main.route('/new-deck', methods=['POST'])
@login_required
def new_deck_post():
    name = request.form['name']
    owner = current_user.id

    # ensure that the user doesn't already have a deck with the requested name
    deck = db.session.execute(db.select(Deck).filter_by(owner=owner,name=name)).scalar()
    if deck:
        flash('a deck with that name exists')
        return redirect(url_for('main.new_deck'))

    # create the new deck
    new_deck = Deck(owner=owner, name=name)
    db.session.add(new_deck)
    db.session.commit()

    return redirect(url_for('main.decks'))

