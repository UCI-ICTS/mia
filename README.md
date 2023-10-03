
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
### Run the application
```python 
source venv/bin/activate
python main.py
```
### Databse migrations
* create a migration script everytime you later your database 
models.
```python
flask db migrate -m "Your message here"
```
* Upgrade the database (apply the migration script)
```python
flask db upgrade
```