"""
metabet index (main) view.
URLs include:
/
"""

from curses import meta
import hashlib
import sqlite3
from turtle import update
from click import get_current_context
import flask
import metabet
import os
import pathlib
from metabet.model import get_db
from datetime import datetime
from metabet.views.s3_functions import upload_files, CHOICE_IMAGE_BUCKET, UPLOAD_FOLDER
from werkzeug.utils import secure_filename
from datetime import date, datetime
import pytz

# Return templated profile page
@metabet.app.route('/profile')
def show_profile():
    return flask.render_template('profile.html')

# Index Page: Reroute to poll page
@metabet.app.route('/')
def show_index():
    """Display / route."""

    return flask.redirect(flask.url_for('show_vote'))

# Login Page
@metabet.app.route('/login', methods=['GET'])
def show_login():
    context = {}
    return flask.render_template("login.html", **context)

# POST login
@metabet.app.route('/login', methods=['POST'])
def post_login():
    username = flask.request.form['username']
    password = flask.request.form['password']
    if not username or not password:
        flask.flash("Incorrect username or password")
        return flask.redirect(flask.url_for('show_login'))
    
    query = 'SELECT * from admin WHERE email = {}'.format(sqlify(username))
    conn = get_db()
    result = conn.execute(query)
    
    admins = []
    for admin in result:
        curr = {
            'fullname': admin[2],
            'email': admin[0],
            'password': admin[1]
        }
        admins.append(curr)
    
    if not admins: #currently does not work
        flask.flash("Incorrect username or password")
        return flask.redirect(flask.url_for('show_login'))


    stored_password = admins[0]['password'] #currently does not work
    if check_passwords(stored_password, password):
        # set session if not there
        flask.session['username'] = username
        # login user
    else:
        flask.flash("Incorrect username or password")

    return flask.redirect(flask.url_for('show_poll_management'))


@metabet.app.route('/logout', methods=['POST'])
def logout():
    flask.session.clear()
    return flask.redirect(flask.url_for("show_vote"))


# TODO: add ability to edit tourney?
@metabet.app.route('/tournaments', methods=['GET'])
def show_tourney_page():
    context = {
        'tournaments': get_tournaments()
    }
    return flask.render_template('admin_tournaments.html', **context)

@metabet.app.route('/tournament', methods=['GET'])
def show_tourney_management():
    if "username" not in flask.session.keys():
        return flask.render_template('login.html')
    # add tourney, edit tourney, end tourney, cur tourney details 
    context = {
        'current_tourney': get_current_tournament()
    }
    return flask.render_template('add_tournament.html', **context)

@metabet.app.route('/tournament', methods=['POST'])
def post_tournament():
    start_date = date.today()
    theme = flask.request.form['theme']
    # TODO: add ability for a logo upload
    tourney_exists = False if get_current_tournament() is None else True

    if tourney_exists:
        flask.flash('There is already an active tournament. End current tournament before creating a new one')
        flask.redirect(flask.url_for('show_tourney_management'))

    try:
        add_tournament(start_date=start_date, theme=theme, is_active=True)
    except:
        flask.flash('Error adding tournament. Please Try Again')
        flask.redirect(flask.url_for('show_tourney_management'))

    flask.flash('Tournament Started!')
    return flask.redirect(flask.url_for('show_tourney_page'))

@metabet.app.route('/end_tournament', methods=['POST'])
def end_tourney():
    # display current tournament analytics somewhere --> '/show_tournament_analytics'
    # shows winners
    # TODO: ask to make sure
    # TODO: check that there is no current poll

    try:
        end_tournament()
    except Exception as e:
        print(e)
        flask.flash('Error ending tournament. Try Again')
        flask.redirect(flask.url_for('show_tourney_management'))

    flask.flash('Ended Tournament!')
    return flask.redirect(flask.url_for('show_tourney_management'))

@metabet.app.route('/show_tournament_analytics', methods=['POST'])
def show_tourney_analytics():
    return

# Return add_poll page 
@metabet.app.route('/poll', methods=['GET'])
def show_poll_management():    
    if "username" in flask.session.keys():
        active_poll = get_active_poll_id()
        choices = [] if active_poll == -1 else get_choices(active_poll)
        context = {
            'round_no': get_current_round(),
            'choices': choices
        }
        return flask.render_template('add_poll.html', **context)

    return flask.render_template('login.html')

def get_choices(poll_id):
    query = "SELECT choice FROM choices WHERE poll_id={}".format(sqlify(poll_id))
    result = get_db().execute(query)
    return [row[0] for row in result]

@metabet.app.route('/current_info')
def show_current_info():
    round = get_current_round()
    tournament = get_current_tournament()
    active_poll = get_active_poll_id()
    
    context = {
        'round_no': round,
        'tourney_id': tournament,
        'poll_id': active_poll,
        'choices': []
    }

    return flask.render_template('admin_current_tournament.html', **context)


# POST new poll to db
@metabet.app.route('/poll', methods=['POST'])
def post_poll():
    if "username" not in flask.session.keys():
        flask.abort(403)

    # Retrieve data from submitted poll html form
    poll_date = datetime.strptime(flask.request.form['poll_date'], '%Y-%m-%d')

    #  Localizing end time to EST
    end_time = datetime.strptime(flask.request.form['end_time'], '%Y-%m-%dT%H:%M')

    description = flask.request.form['description']
    redemption_poll = True if flask.request.form.get('redemption') else False

    choices = []
    choice_name = 'choice'

    cur_tournament = get_current_tournament()

    if not cur_tournament:
        flask.flash('There are currently no active tournaments. Please start new tournament before adding a poll.')
        return flask.redirect(flask.url_for('show_tourney_management'))

    # error checking on active tournaments
    current_regular_poll, current_redemption_poll = get_open_polls()
    
    if current_regular_poll or current_redemption_poll:
        flask.flash('There is an active poll. Please add answer to that poll before adding another poll.')
        return flask.redirect(flask.url_for('show_poll_management'))

    choice_image_files = []

    try:
        for i in range(1,6):
            form_name = choice_name + str(i)
            choice = flask.request.form[form_name]
            if choice != '':
                choices.append(choice)
                # TODO: file_name = 'file' + str(i)
                # img_file = flask.request.files[file_name]
                # new_file_name = secure_filename(img_file.filename)
                # uploads_path = pathlib.Path("metabet")/"static"/UPLOAD_FOLDER
                # img_file.save(os.path.join(uploads_path, new_file_name))
                # choice_image_files.append(f"{uploads_path}/{new_file_name}")
    except Exception as e:
        print(e)
        flask.flash("Error adding choices/images to database/S3. Try Again.")
        return flask.redirect(flask.url_for('show_poll_management'))

    try:
        # add poll to db
        add_poll(date=poll_date, description=description, end_time=end_time, tournament_id=cur_tournament, round_no=get_current_round(), redemption=redemption_poll)
    except Exception as e:
        print(e)
        flask.flash('Error Adding Poll: Database Error')
        return flask.redirect(flask.url_for('show_poll_management'))

    poll_id = get_poll_id(get_current_tournament(), get_current_round(), redemption_poll)

    try:
        add_choices(poll_date, choices, choice_image_files, poll_id)
    except Exception as e:
        print(e)
        delete_choices(poll_id)
        delete_poll(poll_date)
        flask.flash("Error adding choices/images to database/S3. Try Again.")
        return flask.redirect(flask.url_for('show_poll_management'))

    # set active poll to current
    set_active_poll(poll_id)
    
    flask.flash('Poll Added!')
    return flask.redirect(flask.url_for('show_poll_management'))

def set_active_poll(poll_id):
    query = "UPDATE tournaments SET active_poll = {} WHERE id = {}".format(sqlify(poll_id), sqlify(get_current_tournament()))
    conn = get_db()
    conn.execute(query)

def delete_choices(poll_id):
    query = "DELETE FROM choices WHERE poll_id = {}".format(sqlify(poll_id))
    conn = get_db()
    conn.execute(query)

# Add correct answer for a given poll to poll db
@metabet.app.route('/add_answer', methods=['POST'])
def post_correct_answer():
    if(get_active_poll_id() == -1):
        flask.flash("There are no active polls. Please add a poll before adding correct answer")
        return flask.redirect(flask.url_for('show_poll_management'))

    if('choices' not in flask.request.form.keys()):
        flask.flash("Please select a correct answer")
        return flask.redirect(flask.url_for('show_poll_management'))

    correct = flask.request.form['choices']
    try:
        add_correct_choice(correct)
        update_user_standing(get_current_round(), redemption=active_poll_is_redemption())
        # set active poll to -1
        set_active_poll(-1)
        # update round number
        set_current_round(get_current_round() + 1)
    except:
        flask.flash('Error adding correct choice to Database')

    flask.flash("We are now in round {}".format(get_current_round()))
    return flask.redirect(flask.url_for('show_poll_management'))

# returns True if active poll is a redemption poll
def active_poll_is_redemption():
    query = "SELECT redemption_poll FROM polls WHERE id={}".format(sqlify(get_active_poll_id))
    conn = get_db()
    result = conn.execute(query)

    is_redemption = False
    for row in result:
        is_redemption = True if row[0] == 1 else False

    return is_redemption

def set_current_round(round):
    query = "UPDATE tournaments SET current_round={} WHERE id={}".format(sqlify(round), sqlify(get_current_tournament()))
    conn = get_db()
    conn.execute(query)

# Check if poll exists for specified day
def poll_exists(date):
    query = 'SELECT COUNT(*) from polls WHERE poll_date = {}'.format(sqlify(date))
    conn = get_db()
    result = conn.execute(query)

    for row in result:
        exists = True if row[0] == 1 else False
        if exists:
            print('Poll exists for date: {}'.format(date))
    
    return exists

# Return user poll page (mostly filled with front-end React)
@metabet.app.route('/vote', methods=['GET'])
def show_vote():
    context = {}
    return flask.render_template('vote.html', **context)

@metabet.app.route('/rules', methods=['GET'])
def show_rules():
    context = {}
    return flask.render_template('rules.html', **context)

# Return number of nfts that current user owns from nft table
def get_num_nfts(user_id):
    conn = get_db()
    query = 'SELECT COUNT(*) FROM owners o, nfts n WHERE o.user_id = n.owner AND o.user_id = {}'.format(sqlify(user_id))
    result = conn.execute(query)

    for row in result:
        owns = row[0]

    return owns

# Add entry to nft owner table 
def add_nft_owner(nft_id, owner, position):
    conn = get_db()
    query = 'INSERT INTO nfts VALUES({},{},{})'.format(sqlify(nft_id), sqlify(owner), sqlify(position))
    conn.execute(query)

# Add user to users (accounts) table
def add_owner(user, hashed_password, num_owns=1):
    conn = get_db()
    query = 'INSERT INTO owners (`user_id`,`password`,`num_owns`) VALUES ({},{},{})'.format(sqlify(user),sqlify(hashed_password),num_owns)
    conn.execute(query)

# Add specified poll to poll db 
def add_poll(date, description, end_time, redemption=False, tournament_id=None, round_no=None):

    if tournament_id and round_no:
        query = "INSERT INTO polls (`poll_date`, `description`, `end_time`, `redemption_poll`, `tournament_id`, `round`) \
            VALUES ({},{},{},{},{},{})".format(sqlify(date), sqlify(description), sqlify(end_time), redemption, sqlify(tournament_id), sqlify(round_no))
    elif tournament_id and not round_no:
        query = "INSERT INTO polls (`poll_date`, `description`, `end_time`, `redemption_poll`, `tournament_id`) \
            VALUES ({},{},{},{},{})".format(sqlify(date), sqlify(description), sqlify(end_time), redemption, sqlify(tournament_id))
    elif not tournament_id and round_no:
        query = "INSERT INTO polls (`poll_date`, `description`, `end_time`, `redemption_poll`, `round`) \
            VALUES ({},{},{},{},{})".format(sqlify(date), sqlify(description), sqlify(end_time), redemption, sqlify(round_no))
    else:
        query = "INSERT INTO polls (`poll_date`, `description`, `end_time`, `redemption_poll`) \
            VALUES ({},{},{},{})".format(sqlify(date), sqlify(description), sqlify(end_time), redemption)

    conn = get_db()
    conn.execute(query)
    print("Added poll for date: ".format(date))

# Delete poll with specified date from polls db
def delete_poll(date):
    query = "DELETE from polls WHERE poll_date = {} ".format(sqlify(date))
    conn = get_db()
    conn.execute(query)
    print("Deleted poll for date: ".format(date))


# Add specified choices to choices db table with poll_date == date
def add_choices(date, choices, choice_images, poll_id):
    conn = get_db()
    for i in range(len(choices)):
        # query = 'INSERT INTO choices VALUES ({},{},{})'.format(sqlify(date),sqlify(choices[i]),sqlify(choice_images[i]))
        query = 'INSERT INTO choices VALUES ({},{},{},{})'.format(sqlify(date),sqlify(choices[i]),sqlify('test_img.jpg'), sqlify(poll_id))

        conn.execute(query)
        print("Added choice {} for poll on date: {}".format(choices[i], date))
    # TODO: upload_files(choice_images, CHOICE_IMAGE_BUCKET)

# Add correct choice for active poll
def add_correct_choice(answer):
    query = "UPDATE polls SET correct_answer = {} WHERE id = {}".format(sqlify(answer), sqlify(get_active_poll_id()))
    conn = get_db()
    conn.execute(query)
    print("Added answer: {} to poll with id: {}".format(answer, get_active_poll_id()))

def get_current_round():
    query = "SELECT current_round FROM tournaments WHERE id = {}".format(sqlify(get_current_tournament()))
    conn = get_db()
    result = conn.execute(query)

    for row in result:
        return row[0]
    
    return None

def add_tournament(start_date=date.today(), theme='', logo='', is_active=True):
        query = "INSERT INTO tournaments (`start_date`, `theme`, `logo`, `is_active`, `active_poll`) \
            VALUES ({},{},{},{},{})".format(sqlify(start_date), sqlify(theme), sqlify(logo), is_active, sqlify(-1))
        conn = get_db()
        conn.execute(query)

        # TODO: lock in users nfts and info --> add to user_entries table


def end_tournament():
    # end the current tournament
    query = 'UPDATE tournaments SET is_active = {} WHERE id={}'.format(False, sqlify(get_current_tournament()))
    conn = get_db()
    conn.execute(query)


def get_alive(tournament_id=None):
    cur_tournament = get_current_tournament() if not tournament_id else tournament_id

    if not cur_tournament:
        return []
    
    query = "SELECT metamask_id FROM user_entries WHERE tournament_id = {} AND is_alive = {}".format(sqlify(cur_tournament), True)
    conn = get_db()
    result = conn.execute(query)

    alive_users = [row[0] for row in result]

    return alive_users


# should be called when a correct answer is added to a poll (if redemption answer --> set redemption=True)
def update_user_standing(cur_round, redemption=False):
    # get alive users or alive redemption users
    users = get_alive() if not redemption else get_redemption_users()

    # get correct answer for round
    correct_answer, poll_id = get_correct_answer(get_current_tournament(), cur_round) 


    if redemption:
        # deal with people who used redemption
        for user in users:
            if get_user_answer(user, poll_id) == correct_answer:
                set_in_redemption(user, False)
                set_num_user_votes(user, 1)
                set_used_redemption(user, True)
            else:
                set_user_not_alive(user)
    else:
        # logic for regular poll and is_alive users
        for user in users:
            if get_user_answer(user, poll_id) != correct_answer:
                # decrease num_user_votes by 1
                decrease_user_votes(user, value=1)
                if get_num_votes_left(user) == 0:
                    # only allow redemption after round 1
                    if get_used_redemption(user) or cur_round > 1:
                        set_user_not_alive()
                    else:
                        set_in_redemption(user, True)

    return

def get_used_redemption(user_id):
    query = "SELECT * FROM user_entries WHERE metamask_id = {} AND tournament_id = {}".format(sqlify(user_id), sqlify(get_current_tournament()))
    conn = get_db()
    result = conn.execute(query)

    used_redemption = None

    for row in result:
        used_redemption = row[3]

    return True if used_redemption == 1 else False   

# Sets used_redemption value to new_value for current tournament and given user_id
def set_used_redemption(user_id, new_value=True):
    query = "UPDATE user_entries SET used_redemption = {} WHERE metamask_id = {} AND tournament_id = {}".format(new_value, sqlify(user_id), sqlify(get_current_tournament()))
    conn = get_db()
    conn.execute(query)    

# Sets in redemption value to new_value for current tournament and given user_id
def set_in_redemption(user_id, new_value=True):
    query = "UPDATE user_entries SET in_redemption = {} WHERE metamask_id = {} AND tournament_id = {}".format(new_value, sqlify(user_id), sqlify(get_current_tournament()))
    conn = get_db()
    conn.execute(query)

# decrease number of user votes in user_entries by value provided
def decrease_user_votes(user_id, value=1):
    query = "UPDATE user_entries SET votes_left = votes_left - {} WHERE metamask_id = {} AND tournament_id = {}".format(sqlify(value), sqlify(user_id), sqlify(get_current_tournament()))
    conn = get_db()
    conn.execute(query)

def set_num_user_votes(user_id, value=1):
    query = "UPDATE user_entries SET votes_left = {} WHERE metamask_id = {} AND tournament_id = {}".format(sqlify(value), sqlify(user_id), sqlify(get_current_tournament()))
    conn = get_db()
    conn.execute(query)

def get_num_votes_left(user_id):
    query = "SELECT * FROM user_entries WHERE metamask_id = {} AND tournament_id = {}".format(sqlify(user_id), sqlify(get_current_tournament()))
    conn = get_db()
    result = conn.execute(query)

    num_votes = 0

    for row in result:
        num_votes = row[5]

    return num_votes

# returns (regular poll, redemption poll) for current round or (None,None) if none exist for current round
def get_open_polls():
    query = "SELECT * FROM polls WHERE tournament_id = {} AND round = {}".format(sqlify(get_current_tournament()), sqlify(get_current_round()))
    conn = get_db()
    result = conn.execute(query)

    redemption = regular = None

    for row in result:
        if row[3] == 1:
            print("redemption poll with id: {}".format(row[0]))
            redemption = row[0]
        else:
            print("regular poll with id: {}".format(row[0]))
            regular = row[0]

    return regular, redemption


def set_user_not_alive(user_id):
    query = "UPDATE user_entries SET is_alive = {} WHERE metamask_id = {}".format(False, sqlify(user_id))
    conn = get_db()
    conn.execute(query)

def get_user_answer(user_id, poll_id):
    query = "SELECT choice FROM user_votes WHERE user_id = {} AND poll_id = {}".format(sqlify(user_id), sqlify(poll_id))
    conn = get_db()
    result = conn.execute(query)

    for row in result:
        return row[0]
    
    return None

def get_redemption_users():
    query = "SELECT metamask_id FROM user_entries WHERE tournament_id = {} AND in_redemption = {}".format(sqlify(get_current_tournament()), True)
    conn = get_db()
    result = conn.execute(query)

    redemption_users = [row[0] for row in result]   

    return redemption_users

def get_correct_answer(tournament_id, round, redemption_answer=False):
    conn = get_db()
    query = "SELECT id, correct_answer FROM polls WHERE tournament_id = {} AND round = {}".format(sqlify(tournament_id), sqlify(round))
    result = conn.execute(query)    

    for row in result:
        poll_id = row[0]
        correct_answer = row[1]

    return correct_answer, poll_id

def get_tournaments():
    query = 'SELECT * from tournaments ORDER BY id desc'
    conn = get_db()
    result = conn.execute(query)

    tournaments = []

    for row in result:
        cur_tourney = {
            'id': row[0],
            'start_date': row[1],
            'theme': row[2],
            'logo': row[3],
            'is_active': row[4]
        }
        tournaments.append(cur_tourney)

    print(tournaments)
    return tournaments

def get_poll_id(tournament_id, round_no, redemption):
    query = "SELECT id FROM polls WHERE tournament_id={} AND round={} AND redemption_poll={}".format(sqlify(tournament_id), sqlify(round_no), redemption)
    conn = get_db()
    result = conn.execute(query)

    for row in result:
        return row[0]
    
    return None

def delete_choices(poll_id):
    query = "DELETE FROM choices WHERE poll_id = {}".format(sqlify(poll_id))
    conn = get_db()
    conn.execute(query)
    
#checks passwords for admin login
def check_passwords(real, inp):
    """Check password is valid."""
    alg = real.split('$')
    algorithm = alg[0]
    salt = alg[1]
    hash_obj = hashlib.new(algorithm)
    password_salted = salt + inp
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    password_db_string = "$".join([algorithm, salt, password_hash])
    if password_db_string == real:
        return True
    return False

def get_current_tournament():
    query = "SELECT id FROM tournaments WHERE is_active = {}".format(True)
    conn = get_db()
    result = conn.execute(query)

    cur_tourney = None
    
    for row in result:
        cur_tourney = row[0]

    return cur_tourney

# get active poll -- return -1 if none 
def get_active_poll_id():
    query = "SELECT active_poll FROM tournaments WHERE is_active = {}".format(True)
    conn = get_db()
    result = conn.execute(query)

    cur_poll = None
    
    for row in result:
        cur_poll = row[0]

    return cur_poll

# Add quotes to values for MySQL (neccesary to insert into db)
def sqlify(word):
    return '\'' + str(word) + '\''

