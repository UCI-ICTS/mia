## Install with AWS Cloud Formation
* Add your Github deploy secret key to AWS SecretsManager. Add the private key as plaintext.
  * name the key /mia/ssh/key (if you change this name, you need to update the cloudformation template)
  * copy the ARN for the Secret into the cloudformation template
* You need to create an ec2 keypair
* Navigate to Cloud Formation and create a new stack using the template in this repo (with updated parameters)
* Run the Cloud Formation Stack
  * Remember to keep track of the database password
* Log into the ec2 instance (for simplicity I connected directly from the console)
* Run the following commands:
```python
cd /home/ubuntu/mia

nano .miaenv
# fill out this info and save the file (double check parameters are correct)
FLASK_ENV=prd
FLASK_RUN_HOST=<IP ADDRESS FOR EC2 INSTANCE>
FLASK_RUN_PORT=5001
SECRET_KEY=<ADD_A_SECRET_KEY (E.G., UUID)>
PRD_DATABASE_URL=postgresql://pgadmin:<DATABASE_PASSWORD>@miaprdpostgresdb.cb6yykkuuahw.us-east-1.rds.amazonaws.com:5432/mia_app
# save the file

sudo systemctl restart mia

source/venv/bin/activate

flask db upgrade

# launch ipython and create an admin login account
ipython -i setup_ipython.py

In [1]: member = Members(full_name='John Smith', email='jsmith@hs.uci.edu', role=MemberRoleGroup.ADMIN, password='#SomethingSuperSecure')

In [2]: db.session.add(member)

In [3]: db.session.commit()

In [4]: exit

# you're done!
exit
```
* You should be able to go to the http://IP_ADDRESS and log into the site. Need to configure https with other certificates.
## Install & Setup (Local or within an EC2 instance)
* These instructions are for MacOS (Windows is possible but slightly different)
* Download and install PostgreSQL (v16)
  * For Ubuntu, install with apt `sudo apt-get install postgresql`
  * Configure a password for the default `postgres` user:
    * Open a psql shell with the postgres user with: `sudo -u postgres psql`.
    * At the `postgres=#` prompt, type `\password` to set the password for the default `postgres` user.
    * Follow the prompts and enter the new password. Save it for the `.miaenv` config file.
    * Create two databases `mia_app` and `test_db` in psql with:
      * `CREATE DATABASE mia_app ;`
      * `CREATE DATABASE test_db ;`
      * Don't forget the `;` after each SQL statement.
    * [Optional] If ufw (uncomplicated firewall) is enabled and running, allow ports 80 and 443 for the web server with:
      * `sudo ufw allow 80/tcp`
      * `sudo ufw allow 443/tcp`

* git clone the repo
  * Create a `.miaenv` file in the repo directory
  * Generate a secret key with `python3 -c "import os ; print(os.urandom(24)"`. Copy the string between the quotes.
  * The file should contain the following information:
  ```python
  FLASK_ENV=local  # local, dev or prd
  FLASK_RUN_HOST=0.0.0.0  # local IP address for the instance
  FLASK_RUN_PORT=[80 for testing without HTTPS, otherwise 443]
  SECRET_KEY=[change this key with the value above for client-side security]
  DATABASE_URL=postgresql://postgres:postgres@localhost:5432/mia_app  # Change username:password@localhost accordingly to match what was set with psql earlier
  TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/test_db  # Change username:password@localhost accordingly to match what was set with psql earlier
  DEV_DATABASE_URL=[ignored if local or prd is set]
  PRD_DATABASE_URL=[ignored if local or dev is set]
  ```
* create the virtual environment
```python
# create the virtual environment
python3 -m venv venv

# activate virtual environment
source venv/bin/activate

# pip install the requirements
pip3 install -r requirements.txt

# update the database with the definitions in the migrations folder
flask db upgrade
```
Next create the first admin user
```python
# launch ipython and create an admin login account
ipython -i setup_ipython.py

In [1]: member = Members(full_name='John Smith', email='jsmith@hs.uci.edu', role=MemberRoleGroup.ADMIN, password='#SomethingSuperSecure')

In [2]: db.session.add(member)

In [3]: db.session.commit()
```

## Run the application (in a new tab)
```python 
source venv/bin/activate
sudo venv/bin/python mia.py

# go to the admin page and login
http://[aws-ec2-instance-ip-address]/admin/
```
## How to use the application
### 1. Create a script
#### Once you create a new script, you can select "Edit script content" and upload the JSON file in this repo instead of doing it through the command line
First create a script that you can assign to users. The application comes with a consent script 
JSON file to get started.
```python
http://[aws-ec2-instance-ip-address]/admin/scripts/
```
Click `Add New Script` and provide the name "PMGRC Consent" with a description "PMGRC GREGoR consent script"

![img.png](app/static/images/readme/scripts_admin.png)
Launch ipython
```python
# launch ipython and create an admin login account
ipython -i setup_ipython.py

In [4]: _replace_db_script_with_json('PMGRC Consent', 'PMGRC Consent.json')
```
This will load the current consent script into the database.

### 2. Create users
Navigate to the `Users` and click `Add New User`
```python
http://[aws-ec2-instance-ip-address]/admin/users/
```
![img.png](app/static/images/readme/users_admin.png)

### 3. Get the user invite link
Click on `More Options` and select `Get chat invite link`. Copy the link and paste it into a new browser tab.

![img.png](app/static/images/readme/user_chat_link.png)

Start the consent chat
![img.png](app/static/images/readme/consent_chat.png)

## Developer Information
### Run the tests
```python
# from the project directory
source venv/bin/activate
pytest
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
# launch an ipython session with access to all the models
ipython -i setup_ipython.py
```
