# MIA `.secrets` Configuration

Below is an example configuration file. This file contains sensitive information and deployment specific settings. Example values and specific instructions are given in each of the respective [deployment](docs/deployment) instructions.

See the [Django docs](https://docs.djangoproject.com/en/5.0/ref/settings/) for more specific details.
``` shell
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
STATIC_URL=/Users/hadleyking/GitHub/UCI-GREGoR/mia/server/static/
STATIC_ROOT=static
MEDIA_URL=/Users/hadleyking/GitHub/UCI-GREGoR/mia/server/media/
MEDIA_ROOT=media
```


##  DJANGO_KEYS: Keys and Tokens for Django
### SECRET_KEY
According to the Django docs the [SECRETE_KEY](https://docs.djangoproject.com/en/dev/ref/settings/#secret-key) is used for the following:
- All sessions if you are using any other session backend than django.contrib.sessions.backends.cache, or are using the default get_session_auth_hash().
- All messages if you are using CookieStorage or FallbackStorage.
- All PasswordResetView tokens.
- Any usage of cryptographic signing, unless a different key is provided.

If you rotate your secret key, all of the above will be invalidated. Secret keys are not used for passwords of users and key rotation will not affect them.

## SERVER: Deployument specific settings

### DEBUG
Django's [DEBUG](https://docs.djangoproject.com/en/5.0/ref/settings/#debug) flag.

It's a boolean that turns on/off debug mode, with the default as `False`. It is reccomended to never deploy a site into production with DEBUG turned on.

### ALLOWED_HOSTS

Django's [ALLOWED_HOSTS](https://docs.djangoproject.com/en/5.0/ref/settings/#allowed-hosts) list. Default is an empty list. 

"A list of strings representing the host/domain names that this Django site can serve. This is a security measure to prevent HTTP Host header attacks, which are possible even under many seemingly-safe web server configurations."

### CORS_ALLOWED_ORIGINS
A list of origins that are authorized to make cross-site HTTP requests. The origins in this setting will be allowed, and the requesting origin will be echoed back to the client in the `access-control-allow-origin` header. Defaults to []. See the [repo](https://github.com/adamchainz/django-cors-headers) for moe info. 

### SERVER_VERSION
The SERVER_VERSION is displayed on the Swagger Docs page. 

### DASHBOARD_URL
The PUBLIC_HOSTNAME to be returnd in the `user_info` object. This is used by the Dashboard for interacting with a specific instance of the server (i.e. to make requests), and in the Swager Docs. It is also utilized in the API tests.

### EMAIL_BACKEND
Specifies which of Django's [EMAIL_BACKEND](https://docs.djangoproject.com/en/5.0/topics/email/#topic-email-backends) classes to use. 

This app has been tested using the `django.core.mail.backends.smtp.EmailBackend` with `sendmail` and a GMail account in production, and with `django.core.mail.backends.console.EmailBackend` in local deployments. 

##  DATABASE: Keys and Tokens for Django DB 
### ENGINE
The database backend to use. The built-in database backends are:

    'django.db.backends.postgresql'
    'django.db.backends.mysql'
    'django.db.backends.sqlite3'
    'django.db.backends.oracle'

You can use a database backend that doesn’t ship with Django by setting ENGINE to a fully-qualified path (i.e. mypackage.backends.whatever).

### NAME
The name of the database to use. For SQLite, it’s the full path to the database file. When specifying the path, always use forward slashes, even on Windows (e.g. C:/homes/user/mysite/sqlite3.db).

### USER
The username to use when connecting to the database. Not used with SQLite

### PASSWORD
The password to use when connecting to the database. Not used with SQLite.

### HOST
Which host to use when connecting to the database. An empty string means localhost.
### PORT
The port to use when connecting to the database. An empty string means the default port. Not used with SQLite.

### STATIC_URL
URL to use when referring to static files located in STATIC_ROOT.

### STATIC_ROOT
The absolute path to the directory where collectstatic will collect static files for deployment.

### MEDIA_URL
URL that handles the media served from MEDIA_ROOT, used for managing stored files. It must end in a slash if set to a non-empty value. You will need to configure these files to be served in both development and production environments.

### MEDIA_ROOT
Absolute filesystem path to the directory that will hold user-uploaded files.
