"""
Insta485 index (main) view.
URLs include:
/
"""
from xmlrpc.client import boolean
import flask
import metabet
import os
import pathlib
from werkzeug.security import generate_password_hash, check_password_hash
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

    return flask.redirect(flask.url_for('show_vote'))

# TODO: add ability to edit tourney?
@metabet.app.route('/tournaments', methods=['GET'])
def show_tourney_page():
    context = {
        'tournaments': get_tournaments()
    }
    return flask.render_template('admin_tournaments.html', **context)

@metabet.app.route('/tournament', methods=['GET'])
def show_add_tourney():
    return flask.render_template('add_tournament.html')

@metabet.app.route('/tournament', methods=['POST'])
def post_tournament():
    start_date = datetime.strptime(flask.request.form['start_date'], '%Y-%m-%d')
    theme = flask.request.form['poll_theme']
    # TODO: add ability for a logo upload

    add_tournament(start_date=start_date, theme=theme, is_active=False)
    flask.flash('Tournament Added!')
    return flask.redirect(flask.url_for('show_tourney_page'))

# Return add_poll page 
@metabet.app.route('/poll', methods=['GET'])
def show_add_poll():    

    return flask.render_template('add_poll.html')

# POST new poll to db
@metabet.app.route('/poll', methods=['POST'])
def post_poll():
    # Retrieve data from submitted poll html form
    poll_date = datetime.strptime(flask.request.form['poll_date'], '%Y-%m-%d')

    #  Localizing end time to EST
    end_time = datetime.strptime(flask.request.form['end_time'], '%Y-%m-%dT%H:%M')

    description = flask.request.form['description']
    replace = True if flask.request.form.get('replace') else False

    choices = []
    choice_name = 'choice'

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
        return flask.redirect(flask.url_for('show_add_poll'))

    try:
        # check if poll exists
        if poll_exists(poll_date):
            if not replace:
                flask.flash('Poll already exists for this date. Try Again.')
                return flask.redirect(flask.url_for('post_poll'))
            delete_poll(poll_date)

        # add poll to db
        add_poll(poll_date, description, end_time)
    except Exception:
        flask.flash('Error Adding Poll: Database Error')
        return flask.redirect(flask.url_for('show_add_poll'))


    try:
        add_choices(poll_date, choices, choice_image_files)
    except Exception:
        delete_poll(poll_date)
        flask.flash("Error adding choices/images to database/S3. Try Again.")
        return flask.redirect(flask.url_for('show_add_poll'))
    
    flask.flash('Poll Added!')
    return flask.redirect(flask.url_for('show_add_poll'))

# Add correct answer for a given poll to poll db
@metabet.app.route('/add_answer', methods=['POST'])
def post_correct_answer():
    poll_date = datetime.strptime(flask.request.form['poll_date'], '%Y-%m-%d')
    correct = flask.request.form['correct']
    try:
        add_correct_choice(poll_date,correct)
    except:
        flask.flash('Error adding correct choice to Database')

    return flask.redirect(flask.url_for('show_add_poll'))

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

# Return signup page
@metabet.app.route('/signup')
def show_signup():
    return flask.render_template('signup.html')

# POST new signup
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
    try:
        num_owns = get_num_nfts(user_id)
    except Exception:
        flask.flash('Unable to retrieve number of nfts owned from database')
        return flask.redirect(flask.url_for('show_login'))
    if num_owns == 0:
        flask.flash('This Metamask ID does not own a Metabet NFT. Please Try Again')
        return flask.redirect(flask.url_for('show_signup'))

    try:
        add_owner(user=user_id, hashed_password=generate_password_hash(password, method='sha256'), num_owns=num_owns)
    except Exception:
        flask.flash('Error adding user to database')

    return flask.redirect(flask.url_for('show_login'))

# Return user poll page (mostly filled with front-end React)
@metabet.app.route('/vote', methods=['GET'])
def show_vote():
    context = {}
    return flask.render_template('vote.html', **context)

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
            VALUES ({},{},{},{},{},{})".format(sqlify(date), sqlify(description), sqlify(end_time), sqlify(redemption), sqlify(tournament_id), sqlify(round_no))
    elif tournament_id and not round_no:
        query = "INSERT INTO polls (`poll_date`, `description`, `end_time`, `redemption_poll`, `tournament_id`) \
            VALUES ({},{},{},{},{})".format(sqlify(date), sqlify(description), sqlify(end_time), sqlify(redemption), sqlify(tournament_id))
    elif not tournament_id and round_no:
        query = "INSERT INTO polls (`poll_date`, `description`, `end_time`, `redemption_poll`, `round`) \
            VALUES ({},{},{},{},{})".format(sqlify(date), sqlify(description), sqlify(end_time), sqlify(redemption), sqlify(round_no))
    else:
        query = "INSERT INTO polls (`poll_date`, `description`, `end_time`, `redemption_poll`) \
            VALUES ({},{},{},{})".format(sqlify(date), sqlify(description), sqlify(end_time), sqlify(redemption))

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

def add_tournament(start_date, theme='', logo='', is_active=False):
        query = "INSERT INTO tournaments (`start_date`, `theme`, `logo`, `is_active`) \
            VALUES ({},{},{},{})".format(sqlify(start_date), sqlify(theme), sqlify(logo), is_active)
        conn = get_db()
        conn.execute(query)

def get_tournaments():
    query = 'SELECT * from tournaments'
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

    return tournaments
    

# Add quotes to values for MySQL (neccesary to insert into db)
def sqlify(word):
    print(word)
    if type(word) is boolean:
        word = 0 if False else True
        print(word)
    return '\'' + str(word) + '\''

