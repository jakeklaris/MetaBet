"""
Insta485 index (main) view.
URLs include:
/
"""
from asyncore import poll
import hashlib
import flask
import metabet
from werkzeug.security import generate_password_hash, check_password_hash
from metabet.model import get_db
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
    print(get_db())
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
        flask.abort(400)
    
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

    return flask.redirect(flask.url_for('show_add_poll'))


@metabet.app.route('/logout', methods=['POST'])
def logout():
    flask.session.clear()
    return flask.redirect(flask.url_for("show_vote"))


# Return add_poll page 
@metabet.app.route('/poll', methods=['GET'])
def show_add_poll():    
    if "username" in flask.session.keys():
        return flask.render_template('add_poll.html')
    return flask.render_template('login.html')

# POST new poll to db
@metabet.app.route('/poll', methods=['POST'])
def post_poll():
    if "username" not in flask.session.keys():
        flask.abort(403)
    timezone = pytz.timezone("America/New_York")
    # Retrieve data from submitted poll html form
    poll_date = datetime.strptime(flask.request.form['poll_date'], '%Y-%m-%d')
    #Adding eastern timezone to the end time
    end_time = datetime.strptime(flask.request.form['end_time'], '%Y-%m-%dT%H:%M')
    end_time = timezone.localize(end_time)
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
    add_poll(poll_date, description, end_time)

    # add choices to db
    add_choices(poll_date, choices)

    flask.flash('Poll Added!')
    return flask.redirect(flask.url_for('show_add_poll'))

# Add correct answer for a given poll to poll db
@metabet.app.route('/add_answer', methods=['POST'])
def post_correct_answer():
    poll_date = datetime.strptime(flask.request.form['poll_date'], '%Y-%m-%d')
    correct = flask.request.form['correct']
    add_correct_choice(poll_date,correct)

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
    num_owns = get_num_nfts(user_id)
    if num_owns == 0:
        flask.flash('This Metamask ID does not own a Metabet NFT. Please Try Again')
        return flask.redirect(flask.url_for('show_signup'))

    add_owner(user=user_id, hashed_password=generate_password_hash(password, method='sha256'), num_owns=num_owns)

    return flask.redirect(flask.url_for('show_login'))

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
def add_choices(date, choices):
    conn = get_db()
    for choice in choices:
        query = 'INSERT INTO choices VALUES ({},{})'.format(sqlify(date),sqlify(choice))
        conn.execute(query)
        print("Added choice {} for poll on date: {}".format(choice, date))


# Add correct choice for specified date's poll to polls db
def add_correct_choice(date,answer):
    query = "UPDATE polls SET correct_answer = {} WHERE poll_date = {}".format(sqlify(answer), sqlify(date))
    conn = get_db()
    conn.execute(query)
    print("Added answer: {} to poll on date: {}".format(answer, date))

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


# Add quotes to values for MySQL (neccesary to insert into db)
def sqlify(word):
    return '\'' + str(word) + '\''

