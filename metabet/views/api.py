import flask
import metabet
from datetime import datetime
from metabet.model import get_db
from metabet.views.index import sqlify

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
    context['voted'] = False

    return flask.jsonify(**context), 200

@metabet.app.route('/api/votes/', methods=['GET'])
def user_vote():
    print('hi')
    data = flask.request.get_json()
    print(data)
    user_id = data['user_id']
    print(user_id)
    return

def get_db_poll(date=datetime.date(datetime.now())):
    query = 'SELECT * FROM polls p WHERE p.poll_date = {}'.format(sqlify(date))

    conn = get_db()
    result = conn.execute(query)


    # use arrow to get date into right format

    poll = {}
    for cur in result:
        poll = {
            'date': cur[0],
            'description': cur[1],
            'endTime': cur[3]
        }
        return poll

    return poll


def get_choices(date=datetime.date(datetime.now())):
    query = 'SELECT c.choice FROM polls p, choices c WHERE p.poll_date = {} AND p.poll_date = c.poll_date'.format(sqlify(date))

    conn = get_db()
    result = conn.execute(query)

    choices = []

    for choice in result:
        choices.append(choice[0])

    return choices