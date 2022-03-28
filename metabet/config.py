import pathlib

# Root of this application, useful if it doesn't occupy an entire domain
APPLICATION_ROOT = '/'

# Secret key for encrypting cookies
SECRET_KEY = b'[8\xf1S\xa8c\x0e]8\x08\xea\x83\xff\xa5\xb6\x898\x94\xbd\x12\xc9\\c\x03'
SESSION_COOKIE_NAME = 'login'

SQLALCHEMY_DATABASE_URI = 'sqlite:///friends.db'