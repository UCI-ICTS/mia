import pytest
from sqlalchemy.orm import scoped_session, sessionmaker
from app import create_app, db
from config import TestConfig


@pytest.fixture(scope='session')
def app():
    app = create_app(TestConfig)
    app.secret_key = 'super secret key'
    with app.app_context():
        yield app


@pytest.fixture(scope='session')
def init_database(app):
    # Setup: Create the database tables
    db.create_all()

    yield db  # this is where the testing happens

    # Teardown: Drop all tables after all tests are done
    db.session.remove()
    db.drop_all()


@pytest.fixture(autouse=True)
def session_transaction(app, init_database):
    # Start a transaction
    connection = db.engine.connect()
    transaction = connection.begin()

    # Create a scoped session
    session_factory = scoped_session(sessionmaker(bind=connection))
    db.session = session_factory

    yield  # this is where the testing happens

    db.session.remove()
    transaction.rollback()
    connection.close()
