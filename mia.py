from flask import Flask
import os
from config import Config, DevConfig, TestConfig, ProductionConfig
from app import create_app
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(basedir, '.miaenv')
load_dotenv(dotenv_path)

# Determine which configuration to use based on the FLASK_ENV environment variable
env_config = os.getenv('FLASK_ENV', 'local')  # Default to 'local'
app = create_app(env_config)

# Use HOST, PORT, DEBUG from the configuration
HOST = app.config['HOST']
PORT = app.config['PORT']
DEBUG = app.config['DEBUG']

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)
