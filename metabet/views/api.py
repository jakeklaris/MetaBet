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
    
    try:
        choices = get_choices(date)
    except Exception:
        context = {
            "message": "Unable to retrieve poll",
            "status_code": 400
        }
        return flask.jsonify(**context), 400
    
    context['poll'] = {}
    context['choices'] = choices
    context['poll']['numChoices'] = len(choices)
    
    try:
        context['poll'] = get_db_poll(date)
    except Exception:
        context = {
            "message": "Unable to retrieve poll",
            "status_code": 400
        }
        return flask.jsonify(**context), 400  

    try:
        context['user_id'] = user_id
        context['voted'], context['selection'] = has_voted(user_id)
    except Exception:
        context = {
            "message": "Unable to retrieve user vote",
            "status_code": 400
        }
        return flask.jsonify(**context), 400        

    return flask.jsonify(**context), 200


# Post user's vote on current day's poll to db 
@metabet.app.route('/api/votes/', methods=['POST'])
def user_vote():
    data = flask.request.get_json()

    try:
        add_vote(data['user_id'], data['selection'])
    except Exception:
        context = {
            "message": "Error submitting user vote",
            "status_code": 400
        }
        return flask.jsonify(**context), 400

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
    query = 'SELECT c.choice, c.s3_filename FROM polls p, choices c WHERE p.poll_date = {} AND p.poll_date = c.poll_date'.format(sqlify(date))

    conn = get_db()
    result = conn.execute(query)

    choices = []

    for choice in result:
        choices.append({
            'choiceName': choice[0],
            'avatar': choice[1]
        })

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