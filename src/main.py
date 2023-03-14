from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from . import db
from . import models
from .models import Deck

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    return render_template('index.html')

@main.route('/decks')
@login_required
def decks():

    decks = db.session.execute(db.select(Deck).filter_by(owner=current_user.id).order_by(Deck.name)).scalars().all()

    print(decks)
    print(len(decks))

    return render_template('decks.html', decks=decks)

@main.route('/decks/<int:deck_id>')
@login_required
def deck(deck_id):
    card = None
    return render_template('deck.html', card=card)

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

