from flask_login import UserMixin
from . import db, create_app

class User(UserMixin, db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    email    = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name     = db.Column(db.String(1000))

class Deck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100))

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    front = db.Column(db.UnicodeText)
    back = db.Column(db.UnicodeText)
    due = db.Column(db.DateTime)

