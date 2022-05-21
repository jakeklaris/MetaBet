"""
metabet admin view.
URLs include:
/
"""

import flask
import metabet
from metabet.model import get_db
from werkzeug.utils import secure_filename
from datetime import date, datetime


#provide details about a tournament including polls in the tournament
@metabet.app.route('/tournaments/<tournament_id>', methods=['GET'])
def show_tournament(tournament_id):
    context = {
        'tournaments': get_tournament(tournament_id),
        'polls': get_polls(tournament_id)
    }
    return flask.render_template('admin_tournament_detail.html', **context)

#provide details about a single poll
@metabet.app.route('/polls/<poll_id>', methods=['GET'])
def show_poll(poll_id):
    context = {
        'polls': get_poll(poll_id),
        'responses': "PROVIDE percentages for who chose what"
        # could also include: # of people eliminated
        # tournament/round info (probably on top)

    }
    return flask.render_template('admin_poll_detail.html', **context)

#returns a list of polls for a given tournament id 
def get_polls(tournament_id):
    query = "SELECT * from polls WHERE tournament_id = {} ".format(sqlify(tournament_id))
    conn = get_db()
    result = conn.execute(query)

    polls = []

    for row in result:
        curr = {
            'id': row[0],
            'round': row[2],
            'redemption': row[3],
            'poll_date': row[4],
            'description': row[5],
            'correct_answer': row[6],
            'end_time': row[7],

        }
        polls.append(curr)
    
    return polls

#returns information for a single poll
def get_poll(id):
    query = "SELECT * from polls WHERE id = {} ".format(sqlify(id))
    conn = get_db()
    result = conn.execute(query)

    polls = []

    for row in result:
        curr = {
            'id': row[0],
            'tournament_id': row[1],
            'round': row[2],
            'redemption': row[3],
            'poll_date': row[4],
            'description': row[5],
            'correct_answer': row[6],
            'end_time': row[7],

        }
        polls.append(curr)
    
    return polls

#returns informaiton for a single tournament
def get_tournament(id):
    query = "SELECT * from tournaments WHERE id = {} ".format(sqlify(id))
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


def sqlify(word):
    return '\'' + str(word) + '\''
