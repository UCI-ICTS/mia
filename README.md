
### Install & Setup
* git clone the repo
* create the virtual environment
```python
python3 -m venv venv
```
* pip install the requirements
```python
pip3 install -r requirements.txt
```
### Run the tests
```python
# from the project directory
source venv/bin/activate
pytest
```
### Run the application
```python 
source venv/bin/activate
python mia.py
```
### Databse migrations
* Initialize the migration database (one time only)
```python
flask db init
```
* create a migration script everytime you later your database 
models.
```python
flask db migrate -m "Your message here"
```
* Upgrade the database (apply the migration script)
```python
flask db upgrade
```

### Interact with the database manually
```python
from app.utils.utils import *
from app import *
app.app_context().push()

# create a new user
user = User(first_name=xxx, last_name=yyy, ...)
db.session.add(user)
db.session.commit()

# get a chat_url for a user
user.chat_url
```