import os
basedir = os.path.abspath(os.path.dirname(__file__))


# change this to dotenv
class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    #     'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost:5432/mia_app'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class TestConfig(object):
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost:5432/test_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
