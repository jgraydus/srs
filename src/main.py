from datetime import datetime, timedelta, timezone
from flask import abort, Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from . import db
from . import models
from .models import Card
from .models import Deck

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    return redirect(url_for('main.decks'))

@main.route('/decks')
@login_required
def decks():
    decks = db.session.execute(db.select(Deck).filter_by(owner=current_user.id).order_by(Deck.name)).scalars().all()
    return render_template('decks.html', decks=decks)

@main.route('/decks/<int:deck_id>')
@login_required
def deck(deck_id):
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

@main.route('/decks/<int:deck_id>/cards/<int:card_id>', methods=['POST'])
@login_required
def card_post(deck_id, card_id):
    owner = current_user.id
    deck = db.session.execute(db.select(Deck).filter_by(id=deck_id,owner=owner)).scalar()

    if not deck:
        abort(404)

    card = db.session.execute(db.select(Card).filter_by(id=card_id, deck_id=deck_id)).scalar()

    if not card:
        abort(404)

    command = request.form['command']
    now = datetime.now(timezone.utc)

    if command == 'remembered':
        due = card.due
        interval = card.interval
        card.interval = interval + 1
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

    if command == 'forgot':
        card.due = now + timedelta(minutes=1)
        card.interval = 0

    card.last_seen = now
    db.session.commit()

    return redirect(url_for('main.deck', deck_id=deck_id))

@main.route('/decks/<int:deck_id>/new-card')
@login_required
def new_card(deck_id):
    owner = current_user.id
    deck = db.session.execute(db.select(Deck).filter_by(id=deck_id,owner=owner)).scalar()

    if not deck:
        abort(404)

    return render_template('new-card.html', deck=deck)

@main.route('/decks/<int:deck_id>/new-card', methods=['POST'])
@login_required
def new_card_post(deck_id):
    front = request.form['front']
    back = request.form['back']

    now = datetime.now(timezone.utc)
    card = Card(deck_id=deck_id, front=front, back=back, interval=0, due=now)

    db.session.add(card)
    db.session.commit()

    return redirect(url_for('main.deck', deck_id=deck_id))

@main.route('/new-deck')
@login_required
def new_deck():
    return render_template('new-deck.html')

@main.route('/new-deck', methods=['POST'])
@login_required
def new_deck_post():
    name = request.form['name']
    owner = current_user.id

    deck = db.session.execute(db.select(Deck).filter_by(owner=owner,name=name)).scalar()

    if deck:
        flash('a deck with that name exists')
        return redirect(url_for('main.new_deck'))

    new_deck = Deck(owner=owner, name=name)

    db.session.add(new_deck)
    db.session.commit()

    return redirect(url_for('main.decks'))

