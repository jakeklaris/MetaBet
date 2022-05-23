"""
metabet index (main) view.
URLs include:
/
"""

from asyncore import poll
import hashlib
import sqlite3
from turtle import update
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
    return flask.render_template('add_tournament.html')

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
    if "username" not in flask.session.keys():
        return flask.render_template('login.html')
    
    context = {}
    cur_poll = get_current_poll()
    
    if cur_poll:
        context = cur_poll

    return flask.render_template('add_poll.html', **context)

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
    replace = True if flask.request.form.get('replace') else False

    choices = []
    choice_name = 'choice'

    cur_tournament = get_current_tournament()

    if not cur_tournament:
        flask.flash('There are currently no active tournaments. Please start new tournament before adding a poll.')
        flask.redirect(flask.url_for('show_tourney_management'))

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
        # check if poll exists
        if poll_exists(poll_date):
            if not replace:
                flask.flash('Poll already exists for this date. Try Again.')
                return flask.redirect(flask.url_for('post_poll'))
            delete_poll(poll_date)

        # add poll to db
        add_poll(date=poll_date, description=description, end_time=end_time, tournament_id=cur_tournament,round_no=1)
    except Exception as e:
        print(e)
        flask.flash('Error Adding Poll: Database Error')
        return flask.redirect(flask.url_for('show_poll_management'))


    try:
        add_choices(poll_date, choices, choice_image_files)
    except Exception as e:
        print(e)
        delete_poll(poll_date)
        flask.flash("Error adding choices/images to database/S3. Try Again.")
        return flask.redirect(flask.url_for('show_poll_management'))
    
    flask.flash('Poll Added!')
    return flask.redirect(flask.url_for('show_poll_management'))

# Add correct answer for a given poll to poll db
@metabet.app.route('/add_answer', methods=['POST'])
def post_correct_answer():
    poll_date = datetime.strptime(flask.request.form['poll_date'], '%Y-%m-%d')
    correct = flask.request.form['correct']
    try:
        add_correct_choice(poll_date,correct)
        redemption = True if flask.request.form.get('redemption') else False
        update_user_standing(get_current_round(), redemption)
        # TODO: if all polls for current round are closed --> update round number
    except:
        flask.flash('Error adding correct choice to Database')

    return flask.redirect(flask.url_for('show_poll_management'))

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
def add_choices(date, choices, choice_images):
    conn = get_db()
    for i in range(len(choices)):
        # query = 'INSERT INTO choices VALUES ({},{},{})'.format(sqlify(date),sqlify(choices[i]),sqlify(choice_images[i]))
        query = 'INSERT INTO choices VALUES ({},{},{})'.format(sqlify(date),sqlify(choices[i]),sqlify('test_img.jpg'))

        conn.execute(query)
        print("Added choice {} for poll on date: {}".format(choices[i], date))
    # TODO: upload_files(choice_images, CHOICE_IMAGE_BUCKET)

# Add correct choice for specified date's poll to polls db
def add_correct_choice(date,answer):
    query = "UPDATE polls SET correct_answer = {} WHERE poll_date = {}".format(sqlify(answer), sqlify(date))
    conn = get_db()
    conn.execute(query)
    print("Added answer: {} to poll on date: {}".format(answer, date))

def get_current_round():
    query = "SELECT current_round FROM tournaments WHERE id = {}".format(sqlify(get_current_tournament()))
    conn = get_db()
    result = conn.execute(query)

    for row in result:
        return row[0]
    
    return None

def add_tournament(start_date=date.today(), theme='', logo='', is_active=True):
        query = "INSERT INTO tournaments (`start_date`, `theme`, `logo`, `is_active`) \
            VALUES ({},{},{},{})".format(sqlify(start_date), sqlify(theme), sqlify(logo), is_active)
        conn = get_db()
        conn.execute(query)

        # TODO: lock in users nfts and info --> add to user_entries table


def end_tournament():
    # end the current tournament
    query = 'UPDATE tournaments SET is_active = {} WHERE id={}'.format(True, sqlify(get_current_tournament()))
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
    correct_answer, poll_id = get_correct_answer(get_current_tournament(), cur_round, redemption_answer=redemption) 


    if redemption:
        # deal with people who used redemption
        for user in users:
            if get_user_answer(user, poll_id) == correct_answer:
                # set in_redemption to false, used_redemption to true, votes_left = 1
                pass
            else:
                set_user_not_alive(user)
    else:
        # logic for regular poll and is_alive users
        for user in users:
            if get_user_answer(user, poll_id) != correct_answer:
                # whatever logic goes here for --votes, in_redemption
                pass
        pass


    return

#gets current poll (where time hasnt expired)
#works under assumption that only one poll is active at a time
#TODO: adjust to deal with redemption polls
def get_current_poll():
    now = datetime.now()
    conn = get_db()
    query = "SELECT * FROM polls WHERE end_time > {}".format(sqlify(now))
    result = conn.execute(query)    

    for row in result:
        curr = {}
        curr["poll_id"] = row[0]
        curr["description"] = row[5]
        curr["end_time"] = row[7]
        curr["poll_date"] = row[4]
        curr["choices"] = get_poll_choices(curr["poll_date"]) #TODO: Update this to poll id if we wanna change the choices table
        return curr

def get_poll_choices(poll_date):
    query = "SELECT * FROM choices WHERE poll_date = {}".format(sqlify(poll_date))
    conn = get_db()
    result = conn.execute(query)

    choices = []
    for row in result:
        curr = {}
        curr["choice"] = row[1]
        curr["s3_filename"] = row[2]
        choices.append(curr)
    
    return choices
    
    return None
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
    query = "SELECT id, correct_answer FROM polls WHERE tournament_id = {} AND round = {} AND redemption_poll = {}".format(sqlify(tournament_id), sqlify(round), redemption_answer)
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


# Add quotes to values for MySQL (neccesary to insert into db)
def sqlify(word):
    return '\'' + str(word) + '\''

