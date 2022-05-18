"""Views, one for each Insta485 page."""
import imp
from metabet.views.index import show_login
from metabet.views.index import show_index
from metabet.views.index import post_login
from metabet.views.index import show_add_poll
from metabet.views.index import post_poll
from metabet.views.index import signup
from metabet.views.index import show_signup
from metabet.views.index import show_vote
from metabet.views.api import get_poll
from metabet.views.api import user_vote
from metabet.views.index import show_add_tourney
from metabet.views.index import show_tourney_page
from metabet.views.admin import show_tournament
from metabet.views.admin import show_poll