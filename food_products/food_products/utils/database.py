import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL

database_hostname = os.getenv('AWS_RDS_HOSTNAME')
database_port = os.getenv('AWS_RDS_PORT')
database_name = os.getenv('AWS_RDS_DB_NAME')
database_username = os.getenv('AWS_RDS_USERNAME')
database_password = os.getenv('AWS_RDS_PASSWORD')

database_url = URL('postgresql',
                   username=database_username,
                   password=database_password,
                   host=database_hostname,
                   port=database_port,
                   database=database_name)

Engine = create_engine(database_url, echo=False)
Session = sessionmaker(bind=Engine)


def get_session():
    return Session()


def get_engine():
    return Engine
