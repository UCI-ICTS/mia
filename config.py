import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(basedir, '.miaenv')
load_dotenv(dotenv_path)


class Config(object):
    SECRET_KEY = os.getenv('SECRET_KEY', 'you-will-never-guess')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/mia_app')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    HOST = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_RUN_PORT', 5000))
    DEBUG = True


class DevConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URL')
    DEBUG = True


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/test_db')
    DEBUG = True


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv('PRD_DATABASE_URL')
    DEBUG = False
