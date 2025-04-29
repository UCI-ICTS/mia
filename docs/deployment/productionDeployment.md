# MIA Production Deployment Instructions & Notes

## System Setup
### Requirements
- [Node.js](https://nodejs.org/en)
- [Python 3](https://www.python.org/downloads/)
- [PostgreSQL](https://www.postgresql.org/download/)
- [Nginx](https://nginx.org/en/docs/install.html)
- [PyEnv](https://github.com/pyenv/pyenv) (optional but recommended)
- [Certbot](https://certbot.eff.org/instructions?ws=other&os=ubuntufocal) (optional but recommended)

## System Package Install & Setup
- Set up system users (if needed)
- Install required packages ()
```bash
# update the package list first
sudo dnf update -y
sudo dnf install -y gcc gcc-c++ make openssl-devel bzip2-devel libffi-devel git wget zlib-devel
sudo dnf install git -y
sudo dnf install nodejs -y
sudo dnf install python3.11 -y
sudo dnf install postgresql15 -y
sudo dnf install nginx -y
```

## Install PyEnv (Python Version Manager) [Optional]
```bash
curl https://pyenv.run | bash
```

Then, add these lines to the bottom of your `~/.bashrc` or `~/.bash_profile` (depending on OS):
```bash
# Pyenv configuration
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```

Reload the shell:
```bash
exec "$SHELL"
```
Verify installation:
```bash
pyenv --version
```

## Install & Setup PostgreSQL
### 1. Download and install PostgreSQL (v16)
    sudo dnf install -y postgresql16 postgresql16-server postgresql16-contrib

### 2. Initialize the PostgreSQL database
    sudo postgresql-setup initdb

### 3. Start and enabel the PostgreSQL service
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
#### 3.5 Check the status of the PostgreSQL service
    sudo systemctl status postgresql
### 4. Configure a password for the default `postgres` user
* Open a psql shell with the postgres user 
```bash
sudo -u postgres psql
```
* At the `postgres=#` prompt, type `\password` to set the password for the default `postgres` user.
    * Follow the prompts and enter the new password. Save it somewhere safe (you will need it for your `.secrets` file later).
### 5. Create the MIA database and exit psql
```bash
CREATE DATABASE mia_app;
\q
```

### 6. Allow password authentication for `postgres` 
- Open the pg_hba.conf file:
```bash
sudo nano /var/lib/pgsql/data/pg_hba.conf
```

- Change the PostgreSQL authentication config to use `md5`(passwords) for authentication:
```bash

# TYPE  DATABASE        USER            ADDRESS                 METHOD

# "local" is for Unix domain socket connections only
local   all             all                                     md5
# IPv4 local connections:
host    all             all             127.0.0.1/32            md5
# IPv6 local connections:
host    all             all             ::1/128                 md5
# Allow replication connections from localhost, by a user with the

```
- Save and exit, then restart psql

        sudo systemctl restart postgresql

## Configure the directories and clone the repo
- create a `developers` group
```bash
sudo groupadd developers
```

- Create and then Cofigure the working directory
```
mkdir /var/www/
mkdir /var/www/github
sudo chown -R ec2-user:developers github/
```
- For HTTPS access: 

		git clone https://github.com/UCI-ICTS/mia/

- For SSH access*(RECCOMENDED if you have [SSH keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent) set up)*: 

		git clone git@github.com:UCI-ICTS/mia.git

**Then**

	cd mia/

**If you need to use a branch other than `dev`(the main branch):**

`git switch <BRANCH NAME>` *(for whatever branch you need)*

## MIA Server deployment  (mia/server)

**Open a new terminal and retrun to the project root**

	cd PATH/TO/PROJECT/mia

### Enter the server directory, create a virtual environment, and install the required packages

##### *[pyenv is optional, but can be usefull if there are multiple apps and python versions being used](https://github.com/pyenv/pyenv?tab=readme-ov-file#simple-python-version-management-pyenv)*

	cd server
    pyenv install 3.11.11
	pyenv local 3.11.11
	python3.11 -m venv env
	source env/bin/activate
	pip3.11 install -r requirements.txt

#### Generate the secrets file
----

- Copy the `.secrets.example` to `.secrets`

		cp .secrets.example .secrets

- The `.secrets.example` is set up to run on a local deployment with out modifications. To update the `.secrets` file the required keys are described here: [secrets.md](../secrets.md)
##### *The `EMAIL_BACKEND` should be set to `'django.core.mail.backends.smtp.EmailBackend'` IF you have a [mail server configured](https://medium.com/dajngo/email-configuration-in-django-3c7d9e149445). Otherwise leave the default and the emails will be sent to the log files.*

- Update these parts:

    [DATABASE] section:
    - NAME = mia_app
    - USER = postgres
    - PASSWORD = your-postgres-password
    - HOST = localhost
    - PORT = 5432
    
    [SERVER] section:
    - DEBUG = False
    - ALLOWED_HOSTS = your-public-ip-or-domain
    - EMAIL_BACKEND = 

```
[DJANGO_KEYS]
SECRET_KEY=my_secrete_key

[SERVER]
DEBUG=True
ALLOWED_HOSTS=*
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
SERVER_VERSION=BETA
DASHBOARD_URL=http://localhost:3000/
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

[DATABASE]
ENGINE=django.db.backends.postgresql
NAME=mia_app_local
USER=postgres
PASSWORD=postgres
HOST=localhost
PORT=5432

[STATIC]
STATIC_URL=/PATH/TO/PROJECT/mia/server/static/
STATIC_ROOT=static
MEDIA_URL=/PATH/TO/PROJECT/mia/server/media/
MEDIA_ROOT=media
```

#### Set up DB
---
##### Optional: Create a new DB with fixture data
Create a DB:

	python3 manage.py migrate

Load the DB with test data:

	python manage.py loaddata config/fixtures/local_data.json

---
#### Run Server
`python3 manage.py runserver`

Make sure API is accessible via web browser.

If it worked you should be able to see the API Documentation site at:

`http://localhost:8000/mia/swagger/`

and the Admin site at:

`http://localhost:8000/mia/django-admin/`

Use the following credentials to log in:

````
username: wheel@wheel.sh
password: wheel
````

## MIA Client deployment  (mia/client)

### Enter the repository, create a environment file, and install the required packages

	cd mia/client/

**Install Node packages via Node Package Manager (NPM)**

	npm install

### Update the `.env` file with the required keys: 
	cp .env.example .env

The values for local dev should be:
```
REACT_APP_BASEURL=http://localhost:3000/
REACT_APP_MIADB=http://localhost:8000/
```

### **Start service**

`npm run start`

This will open `http://localhost:3000/` in your default webbrowser if everything went according to plan. If not, see the [troubleshooting tips](troubleshooting.md).

This terminal will be serving the React frontend.
