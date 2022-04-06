"""Views, one for each Insta485 page."""
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