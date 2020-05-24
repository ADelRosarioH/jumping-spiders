from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL


def get_session(connection_string):
    engine = get_engine(connection_string)
    Session = sessionmaker(bind=engine)
    return Session()


def get_engine(connection_string):
    Engine = create_engine(connection_string, echo=False)
    return Engine
