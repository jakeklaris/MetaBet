"""
Insta485 index (main) view.
URLs include:
/
"""
import re
import flask
import metabet
from metabet.model import get_db

@metabet.app.route('/')
def show_index():
    """Display / route."""
    print(get_db())
    return flask.redirect(flask.url_for('post_login'))

@metabet.app.route('/login', methods=['GET'])
def show_login():
    context = {}
    return flask.render_template("login.html", **context)

@metabet.app.route('/login', methods=['POST'])
def post_login():
    # make sure user can log in


    return flask.redirect(flask.url_for('show_vote'))

@metabet.app.route('/poll', methods=['GET', 'POST'])
def show_vote():
    context = {}
    if flask.request.method == 'POST':
        context = {'post': 'POST REQUEST'}
    return flask.render_template('vote.html', **context)