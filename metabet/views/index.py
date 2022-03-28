"""
Insta485 index (main) view.
URLs include:
/
"""
import flask
import metabet

@metabet.app.route('/')
def show_index():
    """Display / route."""
    return flask.redirect(flask.url_for('post_login'))

@metabet.app.route('/login', methods=['GET'])
def show_login():
    context = {}
    return flask.render_template("login.html", **context)

@metabet.app.route('/login', methods=['POST'])
def post_login():
    # make sure user can log in


    return flask.redirect(flask.url_for('show_vote'))

@metabet.app.route('/poll', methods=['GET'])
def show_vote():
    context = {}
    return flask.render_template('vote.html', **context)