# MIA Local Deployment Instructions & Notes

## System Setup
### Requirements
- [Node.js](https://nodejs.org/en)
- [Python 3](https://www.python.org/downloads/)
- [PostgreSQL](https://www.postgresql.org/download/)
- [PyEnv](https://github.com/pyenv/pyenv) (optional but recommended)

## Install & Setup PostgreSQL
### Download and install PostgreSQL (v16)

#### For Ubuntu, install with apt:
     `sudo apt-get install postgresql`

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

#### For MacOS, install with Homebrew:
    `brew install postgresql`

- Connect and create the DB:

        psql postgres
        CREATE DATABASE mia_app;
        \q

## Clone the repo

- For HTTPS access: 

		git clone https://github.com/UCI-ICTS/mia/

- For SSH access*(RECCOMENDED)*: 

		git@github.com:UCI-ICTS/mia.git

**Then**

	cd mia/

**If you need to use a branch other than `dev`(the main branch):**

`git switch <BRANCH NAME>` *(for whatever branch you need)*

## MIA Server deployment  (mia/server)

**Open a new terminal and retrun to the project root**

	cd PATH/TO/PROJECT/mia

### Enter the server directory, create a virtual environment, and install the required packages

##### For Mac/Linux: *[pyenv(optional)](https://github.com/pyenv/pyenv?tab=readme-ov-file#simple-python-version-management-pyenv)*

	cd server
	pyenv local 3.11.1 
	python3 -m venv env
	source env/bin/activate
	pip3.9 install -r requirements.txt

##### For Windows:

	cd server
	python -m venv env
	source env/Scripts/activate
	pip install -r requirements.txt


#### Generate the secrets file
----

- Copy the `.secrets.example` to `.secrets`

		cp .secrets.example .secrets

- The `.secrets.example` is set up to run on a local deployment with out modifications. If you want to update the `.secrets` file the required keys are described here: [secrets.md](../secrets.md)

```
[DJANGO_KEYS]
SECRET_KEY=my_secrete_key

[SERVER]
DEBUG=True
ALLOWED_HOSTS=*
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
SERVER_VERSION=BETA
DASHBOARD_URL=http://localhost:3000/
DATABASE=db.sqlite
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
