from flask import Blueprint, flash, render_template, redirect, request, url_for
from flask_login import login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from . import db

auth = Blueprint('auth', __name__)

#
# show the login page
#
@auth.route('/login')
def login():
    return render_template('login.html')

#
# this route is called by the login form to authenticate the user
#
@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = db.session.execute(db.select(User).filter_by(email=email)).scalar()

    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again')
        return redirect(url_for('auth.login'))

    login_user(user, remember=remember)
    return redirect(url_for('main.decks'))

#
# log out the current user and redirect to index
#
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

#
# show the new user signup form
#
@auth.route('/signup')
def signup():
    return render_template('signup.html')

#
# this route is called by the new user signup form
#
@auth.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    # ensure that there isn't already a user with the given email address
    user = db.session.execute(db.select(User).filter_by(email=email)).scalar()
    if user:
        flash('email address is not available')
        return redirect(url_for('auth.signup'))

    # create a new user
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('auth.login'))

