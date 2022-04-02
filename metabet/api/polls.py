import flask
import metabet

@metabet.app.route('/api/v1/polls/<date>/')
def get_poll(date):
    return