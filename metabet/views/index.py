"""
Insta485 index (main) view.
URLs include:
/
"""
import re
import flask
import flask_login
import metabet
from werkzeug.security import generate_password_hash, check_password_hash
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

@metabet.app.route('/signup')
def show_signup():
    return flask.render_template('signup.html')

@metabet.app.route('/signup', methods=['POST'])
def signup():

    user_id = flask.request.form.get('metamask')
    password = flask.request.form.get('password')
    password_2 = flask.request.form.get('password_copy')

    if password_2 != password:
        flask.flash('Passwords do not match. Try Again.')
        return flask.redirect(flask.url_for('show_signup'))

    # TODO: check user_id owns an nft 

    add_owner(user_id, generate_password_hash(password, method='sha256'))

    return flask.redirect(flask.url_for('show_login'))

def add_owner(user, hashed_password, num_owns=1):
    conn = get_db()
    
    query = 'INSERT INTO owners (`user_id`,`password`,`num_owns`) VALUES ({},{},{})'.format(sqlify_string(user),sqlify_string(hashed_password),num_owns)
    conn.execute(query)

def sqlify_string(word):
    return '\'' + str(word) + '\''