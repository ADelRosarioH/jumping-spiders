from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL


def get_session(host, port, username, password, database):
    engine = get_engine(host, port, username, password, database)
    Session = sessionmaker(bind=engine)
    return Session()


def get_engine(host, port, username, password, database):
    uri = URL('postgresql',
              username=username,
              password=password,
              host=host,
              port=port,
              database=database)
    Engine = create_engine(uri, echo=False)
    return Engine
