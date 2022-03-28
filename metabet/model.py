from metabet import db
from metabet import config
from sqlalchemy import create_engine

def get_db():

    # EXAMPLE USAGE:
    
    # query="describe owners"  
    # my_data=my_conn.execute(query) # SQLAlchemy my_conn result
    # for row in my_data:
    #     print(row) 


    my_conn = create_engine(config.SQLALCHEMY_DATABASE_URI)

    return my_conn

