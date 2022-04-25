import flask
import metabet
from datetime import datetime
from metabet.model import get_db
from metabet.views.index import sqlify
import pytz

# Return JSON with information on current day's poll
@metabet.app.route('/api/vote/<user_id>/', methods=['GET'])
def get_poll(user_id):
    print(user_id)
    context = {}
    date=datetime.date(datetime.now())
    
    choices = get_choices(date)

    return_choices = []
    for choice in choices:
        cur_choice = {
            'choiceName': choice,
            'avatar': '../static/images/heat_image.png'
        }
        return_choices.append(cur_choice)
    

    context['choices'] = return_choices
    context['poll'] = get_db_poll(date)
    context['poll']['numChoices'] = len(return_choices)

    # check if user has voted

    context['user_id'] = user_id
    context['voted'], context['selection'] = has_voted(user_id)

    return flask.jsonify(**context), 200


# Post user's vote on current day's poll to db 
@metabet.app.route('/api/votes/', methods=['POST'])
def user_vote():
    data = flask.request.get_json()
    add_vote(data['user_id'], data['selection'])

    context = {}
    return flask.jsonify(**context), 200

# Retrieve poll from db
def get_db_poll(date=datetime.date(datetime.now())):
    query = 'SELECT * FROM polls p WHERE p.poll_date = {}'.format(sqlify(date))

    conn = get_db()
    result = conn.execute(query)
    timezone = pytz.timezone("America/New_York")

    poll = {}
    for cur in result:
        poll = {
            'date': cur[0],
            'description': cur[1],
            'endTime': timezone.localize(cur[3])
        }
        print("Get from DB")
        print(cur[3])
        return poll

    return poll

# Get choices for this day's poll
def get_choices(date=datetime.date(datetime.now())):
    query = 'SELECT c.choice FROM polls p, choices c WHERE p.poll_date = {} AND p.poll_date = c.poll_date'.format(sqlify(date))

    conn = get_db()
    result = conn.execute(query)

    choices = []

    for choice in result:
        choices.append(choice[0])

    return choices

# Add user vote to db for specified day's poll
def add_vote(user_id, vote, date=datetime.date(datetime.now())):
    query = 'INSERT INTO votes VALUES ({},{},{})'.format(sqlify(user_id), sqlify(date), sqlify(vote))
    conn = get_db()
    conn.execute(query)
    
# Retrieve whether specified user has voted in day's poll from db
def has_voted(user_id, date=datetime.date(datetime.now())):
    query = 'SELECT count(*), v.choice FROM votes v WHERE v.user_id = {} AND v.vote_date = {}'.format(sqlify(user_id), sqlify(date))

    conn = get_db()
    result = conn.execute(query)

    for count in result:
        return (False, '') if (count[0] == 0) else (count[0], count[1])
    
    return False, ''