import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(basedir, '.miaenv')
load_dotenv(dotenv_path)


class Config(object):
    SECRET_KEY = os.getenv('SECRET_KEY', 'you-will-never-guess')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/mia_app')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevConfig(Config):
    # Inherits from Config, can override or add any AWS specific settings
    SQLALCHEMY_DATABASE_URI = os.getenv('AWS_DATABASE_URL')


class TestConfig(object):
    SECRET_KEY = os.getenv('SECRET_KEY', 'you-will-never-guess')
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/test_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
