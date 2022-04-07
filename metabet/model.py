from metabet import db
from metabet import config
from sqlalchemy import create_engine

# Return MySQL DB instance
def get_db():
    my_conn = create_engine(config.SQLALCHEMY_DATABASE_URI)
    return my_conn

