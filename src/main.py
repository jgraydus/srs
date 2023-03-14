from flask import Blueprint, render_template, request
from flask_login import current_user, login_required
from . import db
from . import models

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    return render_template('index.html')

