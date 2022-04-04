"""
Insta485 index (main) view.
URLs include:
/
"""
from asyncore import poll
from crypt import methods
from curses import meta
import re
import flask
import flask_login
from mysqlx import SqlResult
import metabet
from werkzeug.security import generate_password_hash, check_password_hash
from metabet.model import get_db
from datetime import date, datetime

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
    # TODO: make sure user can log in --> has correct password and still owns nft
    # TODO: also retrieve whether they can vote 

    return flask.redirect(flask.url_for('show_vote'))

@metabet.app.route('/poll', methods=['GET'])
def show_add_poll():    

    return flask.render_template('add_poll.html')



@metabet.app.route('/poll', methods=['POST'])
def post_poll():
    poll_date = datetime.strptime(flask.request.form['poll_date'], '%Y-%m-%d')
    description = flask.request.form['description']
    replace = True if flask.request.form.get('replace') else False

    choices = []
    choice_name = 'choice'

    for i in range(1,6):
        form_name = choice_name + str(i)
        choice = flask.request.form[form_name]
        if choice != '':
            choices.append(choice)

    # check if poll exists
    if poll_exists(poll_date):
        if not replace:
            flask.flash('Poll already exists for this date. Try Again.')
            return flask.redirect(flask.url_for('post_poll'))
        delete_poll(poll_date)

    # add poll to db
    add_poll(poll_date, description)

    # add choices to db
    add_choices(poll_date, choices)

    flask.flash('Poll Added!')
    return flask.redirect(flask.url_for('show_add_poll'))

@metabet.app.route('/add_answer', methods=['POST'])
def post_correct_answer():
    poll_date = datetime.strptime(flask.request.form['poll_date'], '%Y-%m-%d')
    correct = flask.request.form['correct']
    add_correct_choice(poll_date,correct)

    return flask.redirect(flask.url_for('show_add_poll'))

def poll_exists(date):
    # check if poll exists for this day 
    query = 'SELECT COUNT(*) from polls WHERE poll_date = {}'.format(sqlify(date))
    conn = get_db()
    result = conn.execute(query)

    for row in result:
        exists = True if row[0] == 1 else False
        if exists:
            print('Poll exists for date: {}'.format(date))
    
    return exists

@metabet.app.route('/signup')
def show_signup():
    return flask.render_template('signup.html')

@metabet.app.route('/signup', methods=['POST'])
def signup():

    user_id = flask.request.form.get('metamask')
    password = flask.request.form.get('password')
    password_2 = flask.request.form.get('password_copy')

    # check if passwords match
    if password_2 != password:
        flask.flash('Passwords do not match. Try Again.')
        return flask.redirect(flask.url_for('show_signup'))

    # check # of nfts that user owns 
    num_owns = get_num_nfts(user_id)
    if num_owns == 0:
        flask.flash('This Metamask ID does not own a Metabet NFT. Please Try Again')
        return flask.redirect(flask.url_for('show_signup'))

    add_owner(user=user_id, hashed_password=generate_password_hash(password, method='sha256'), num_owns=num_owns)

    return flask.redirect(flask.url_for('show_login'))

# ROUTE to show the user the vote -- POSSIBLY AN API
@metabet.app.route('/vote', methods=['GET'])
def show_vote():
    context = {}
    return flask.render_template('vote.html', **context)

# ROUTE for user votes -- POSSIBLY AN API
@metabet.app.route('/vote', methods=['POST'])
def post_vote():
    context = {}
    return flask.render_template('vote.html', **context)

def get_num_nfts(user_id):
    conn = get_db()
    query = 'SELECT COUNT(*) FROM owners o, nfts n WHERE o.user_id = n.owner AND o.user_id = {}'.format(sqlify(user_id))
    result = conn.execute(query)

    for row in result:
        owns = row[0]

    return owns

def add_nft_owner(nft_id, owner, position):
    conn = get_db()
    query = 'INSERT INTO nfts VALUES({},{},{})'.format(sqlify(nft_id), sqlify(owner), sqlify(position))
    conn.execute(query)

def add_owner(user, hashed_password, num_owns=1):
    conn = get_db()
    query = 'INSERT INTO owners (`user_id`,`password`,`num_owns`) VALUES ({},{},{})'.format(sqlify(user),sqlify(hashed_password),num_owns)
    conn.execute(query)

def add_poll(date, description):
    # TODO: add entry to poll db with date=date, description=description, correct=null
    query = "INSERT INTO polls (`poll_date`, `description`) VALUES ({},{})".format(sqlify(date), sqlify(description))
    conn = get_db()
    conn.execute(query)
    print("Added poll for date: ".format(date))

def delete_poll(date):
    query = "DELETE from polls WHERE poll_date = {} ".format(sqlify(date))
    conn = get_db()
    conn.execute(query)
    print("Deleted poll for date: ".format(date))


def add_choices(date, choices):
    # TODO: adds entry to choice db with date=date, choice=choice for choice in choices
    conn = get_db()
    for choice in choices:
        query = 'INSERT INTO choices VALUES ({},{})'.format(sqlify(date),sqlify(choice))
        conn.execute(query)
        print("Added choice {} for poll on date: {}".format(choice, date))


def get_choices(date=datetime.date(datetime.now())):
    query = 'SELECT c.choice FROM polls p, choices c WHERE p.poll_date = {} AND p.poll_date = c.poll_date'.format(sqlify(date))

    conn = get_db()
    result = conn.execute(query)

    choices = []

    for choice in result:
        choices.append(choice[0])

    return choices

def add_correct_choice(date,answer):
    query = "UPDATE polls SET correct_answer = {} WHERE poll_date = {}".format(sqlify(answer), sqlify(date))
    conn = get_db()
    conn.execute(query)
    print("Added answer: {} to poll on date: {}".format(answer, date))

def add_user_vote(user_id, choice):
    now = datetime.date(datetime.now())
    query = 'INSERT INTO votes VALUES({},{},{})'.format(sqlify(user_id), sqlify(now), sqlify(choice))

    conn = get_db()
    conn.execute(query)


def sqlify(word):
    return '\'' + str(word) + '\''
