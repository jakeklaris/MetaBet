import flask
import metabet
from datetime import datetime

@metabet.app.route('/api/v1/polls/')
def get_poll(date):
    return