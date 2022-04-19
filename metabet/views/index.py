"""
Insta485 index (main) view.
URLs include:
/
"""
import os
import pathlib
from tkinter import E
import flask
import metabet
from werkzeug.security import generate_password_hash, check_password_hash
from metabet.model import get_db
from datetime import datetime
from metabet.views.s3_functions import upload_files, CHOICE_IMAGE_BUCKET, UPLOAD_FOLDER
from werkzeug.utils import secure_filename

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
    # TODO: make sure user can log in --> has correct password and still owns nft
    # TODO: also retrieve whether they can vote 

    return flask.redirect(flask.url_for('show_vote'))

# Return add_poll page 
@metabet.app.route('/poll', methods=['GET'])
def show_add_poll():    

    return flask.render_template('add_poll.html')

# POST new poll to db
@metabet.app.route('/poll', methods=['POST'])
def post_poll():
    # Retrieve data from submitted poll html form
    poll_date = datetime.strptime(flask.request.form['poll_date'], '%Y-%m-%d')
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
                file_name = 'file' + str(i)
                img_file = flask.request.files[file_name]
                new_file_name = secure_filename(img_file.filename + str(poll_date))
                uploads_path = pathlib.Path("metabet")/"static"/UPLOAD_FOLDER
                img_file.save(os.path.join(uploads_path, new_file_name))
                choice_image_files.append(f"{uploads_path}/{new_file_name}")
    except Exception:
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


    add_choices(poll_date, choices, choice_image_files)

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
def add_poll(date, description, end_time):
    query = "INSERT INTO polls (`poll_date`, `description`, `end_time`) VALUES ({},{},{})".format(sqlify(date), sqlify(description), sqlify(end_time))
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
        query = 'INSERT INTO choices VALUES ({},{},{})'.format(sqlify(date),sqlify(choices[i]),sqlify(choice_images[i]))
        conn.execute(query)
        print("Added choice {} for poll on date: {}".format(choices[i], date))
    upload_files(choice_images, CHOICE_IMAGE_BUCKET)

# Add correct choice for specified date's poll to polls db
def add_correct_choice(date,answer):
    query = "UPDATE polls SET correct_answer = {} WHERE poll_date = {}".format(sqlify(answer), sqlify(date))
    conn = get_db()
    conn.execute(query)
    print("Added answer: {} to poll on date: {}".format(answer, date))

# Add quotes to values for MySQL (neccesary to insert into db)
def sqlify(word):
    return '\'' + str(word) + '\''

