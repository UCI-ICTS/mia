# MIA Production Deployment Instructions & Notes

## System Setup
### Requirements
- [Node.js](https://nodejs.org/en)
- [Python 3](https://www.python.org/downloads/)
- [PostgreSQL](https://www.postgresql.org/download/)
- [Nginx](https://nginx.org/en/docs/install.html)
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

## Install & Setup PostgreSQL
### 1. Check which PostgreSQL is currently installed (if any), and install
    dnf list installed | grep postgresql

- depending on the output:
  - if a `psql` instance is present (15.0 >) use that. For example if `postgresql15.x86_64` then 
```bash
    sudo dnf install -y postgresql15 postgresql15-server postgresql15-contrib
```

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
sudo vim /var/lib/pgsql/data/pg_hba.conf
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
sudo mkdir /var/www/
sudo mkdir /var/www/github
sudo chown -R ec2-user:developers /var/www/github/
cd /var/www/github/
```
- For HTTPS access: 

		git clone https://github.com/UCI-ICTS/mia/

- For SSH access*(RECCOMENDED if you have [SSH keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent) set up)*: 

		git clone git@github.com:UCI-ICTS/mia.git

**Then**

	cd mia/

**If you need to use a branch other than `dev`(the main branch):**

`git switch <BRANCH NAME>` *(for whatever branch you need)*

## MIA Client deployment  (mia/client)

### Enter the repository, create a environment file, and install the required packages

	cd /var/www/github/mia/client/

**Install Node packages via Node Package Manager (NPM)**

	npm install

### Build the production deployment
```bash
npm run build
```

### Update the `.env` file with the required keys: 
	cp .env.example .env

The values for production should be:
```
REACT_APP_BASEURL=http://[SERVERNAME]
REACT_APP_MIADB=http://[SERVERNAME]
```

## MIA Server deployment  (mia/server)

**Open a new terminal and retrun to the project root**

	cd /var/www/github/mia/server

### Enter the server directory, create a virtual environment, and install the required packages

##### *[pyenv is optional, but can be usefull if there are multiple apps and python versions being used](https://github.com/pyenv/pyenv?tab=readme-ov-file#simple-python-version-management-pyenv)*

	python3.11 -m venv env
	source env/bin/activate
	pip install -r requirements.txt

### Generate the secrets file
----

- Copy the `.secrets.example` to `.secrets`

		cp .secrets.example .secrets

- The `.secrets.example` is set up to run on a local deployment with out modifications. To update the `.secrets` file the required keys are described here: [secrets.md](../secrets.md)
##### *The `EMAIL_BACKEND` should be set to `'django.core.mail.backends.smtp.EmailBackend'` IF you have a [mail server configured](https://medium.com/dajngo/email-configuration-in-django-3c7d9e149445). Otherwise leave the default and the email content will be sent to the log files.*

- To generate a secure Django SECRET_KEY, you can quickly run:
```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

```
- Update these parts:


| Section        | Key                   | What to set                           |
|----------------|------------------------|----------------------------------------|
| `[DJANGO_KEYS]` | `SECRET_KEY`            | Generate a random key (outlined above) |
| `[SERVER]`      | `DEBUG`                 | `False` |
| `[SERVER]`      | `ALLOWED_HOSTS`         | `your-server-public-ip,localhost,127.0.0.1` (replace `your-server-public-ip`) |
| `[DATABASE]`    | `ENGINE`                | `django.db.backends.postgresql` |
| `[DATABASE]`    | `NAME`                  | `mia_app` |
| `[DATABASE]`    | `USER`                  | `postgres` |
| `[DATABASE]`    | `PASSWORD`              | the password you just set for the `postgres` user |
| `[DATABASE]`    | `HOST`                  | `localhost` |
| `[DATABASE]`    | `PORT`                  | `5432` |

### Create a DB:

	python manage.py migrate
---
### Optional: Load DB with test fixture data
Load the DB with test data:

	python manage.py loaddata config/fixtures/initial.json
---

### Collect static files:
```bash
python manage.py collectstatic
```

### Create a Gunicorn log files for MIA
```bash
sudo mkdir /var/log/gunicorn
sudo chown -R nginx:developers /var/log/gunicorn
```

### Create a Gunicorn systemd Service and Socet for MIA
Set up a `systemd` service so Gunicorn runs the Django mia backend at boot and stays running.
```bash
sudo cp ../admin/mia.service /etc/systemd/system/mia.service
sudo cp /var/www/github/mia/admin/mia.socket /etc/systemd/system/mia.socket
sudo chown nginx:developers /var/run/mia.sock
```
Things to check carefully:
- WorkingDirectory — where your Django manage.py lives.
- Environment — path to your virtual environment's bin/.
- ExecStart — run gunicorn, binding to a socket file .sock.
- User/group - the default user is `nginx` but you may need to change this. 

#### Reload systemd so it knows about your new service:

```bash
sudo systemctl daemon-reload
```

#### Start Gunicorn:

```bash
sudo systemctl start mia
```

#### Enable it to auto-start on reboot:
```bash
sudo systemctl enable mia
```
#### Check Gunicorn status:
```bash
sudo systemctl status mia
```

It should say **active (running)**:
```bash
● mia.service - MIA gunicorn daemon
     Loaded: loaded (/etc/systemd/system/mia.service; enabled; preset: disabled)
     Active: active (running) since Tue 2025-04-29 13:25:07 UTC; 3min 20s ago
TriggeredBy: ● mia.socket
   Main PID: 97545 (python)
      Tasks: 4 (limit: 1111)
     Memory: 113.7M
        CPU: 822ms
     CGroup: /system.slice/mia.service
             ├─97545 /var/www/github/mia/server/env/bin/python /var/www/github/mia/server/env/bin/gunicorn --access-logfile /var/log/gunicorn/mia_stdout.log --log-level=debug --log-file /var/log/gunicorn/mia_stderr.log --workers 3 --bind unix:/var/run/mia.sock config.wsgi:applicati>
             ├─97553 /var/www/github/mia/server/env/bin/python /var/www/github/mia/server/env/bin/gunicorn --access-logfile /var/log/gunicorn/mia_stdout.log --log-level=debug --log-file /var/log/gunicorn/mia_stderr.log --workers 3 --bind unix:/var/run/mia.sock config.wsgi:applicati>
             ├─97554 /var/www/github/mia/server/env/bin/python /var/www/github/mia/server/env/bin/gunicorn --access-logfile /var/log/gunicorn/mia_stdout.log --log-level=debug --log-file /var/log/gunicorn/mia_stderr.log --workers 3 --bind unix:/var/run/mia.sock config.wsgi:applicati>
             └─97555 /var/www/github/mia/server/env/bin/python /var/www/github/mia/server/env/bin/gunicorn --access-logfile /var/log/gunicorn/mia_stdout.log --log-level=debug --log-file /var/log/gunicorn/mia_stderr.log --workers 3 --bind unix:/var/run/mia.sock config.wsgi:applicati>
```

### Create the Nginx config for mia
We set up Nginx to proxy to the Gunicorn socket. There are two example files:
1. admin/mia_nocert.conf: for deployment with no server certification
2. admin/mia.conf: for deployment with server certification

#### Copy your updated file to the system Nginx conf and test:
```bash
sudo cp mia/admin/mia.conf /etc/nginx/conf.d/mia.conf
sudo nginx -t
```

#### Check Server

Make sure API is accessible via web browser.

If it worked you should be able to see the API Documentation site at:

`http://[public IP or domain]/mia/swagger/`

and the Admin site at:

`http://[public IP or domain]/mia/django-admin/`

Use the following credentials to log in if you loaded the test data:

````
username: wheel@wheel.tst
password: wheel
````
