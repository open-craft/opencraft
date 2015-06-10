OpenCraft
=========

Install
-------

Instructions based on Ubuntu 14.04.

Install the system package dependencies & virtualenv:

```
$ sudo apt-get install `cat debian_packages.lst`
$ pip3 install --user virtualenv && pip3 install --user virtualenvwrapper
```

Ensure you load virtualenv with Python 3 in `~/.bashrc`:

```
export PATH="$PATH:$HOME/.local/bin" VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
source $HOME/.local/bin/virtualenvwrapper.sh
```

Then reload `~/.bashrc`, create the virtual env and install the Python requirements:

```
$ . ~/.bashrc
$ mkvirtualenv -p /usr/bin/python3 opencraft
$ pip install -r requirements.txt
```


Configure
---------

### Configuration via environment

Create an `.env` file at the root of the repository or set environment variables, customizing the
settings from `opencraft/settings.py` which are loaded via `env()`.

### Ansible worker queue

Install ansible and the configuration repository:

```
$ deactivate && mkvirtualenv -p /usr/bin/python edx-platform # It needs to be Python2 for ansible
$ cd .. # Go outside of the current repository
$ git clone https://github.com/edx/configuration.git
$ cd configuration
$ mkvirtualenv edx-configuration
$ pip install -r requirements.txt
```


Run
---

First ensure that your migrations and static files are up to date:

```
$ honcho run ./manage.py migrate
$ honcho run ./manage.py collectstatic --noinput
```

Then to run the production server:

```
$ honcho start
```

Or for the development server:

```
$ honcho start -f Procfile.dev
```

This runs three processus (via honcho which reads `Procfile`):

* *web*: the main HTTP server (Django - Werkzeug debugger in dev, gunicorn in prod)
* *websocket*: the websocket server (Tornado)
* *worker*: runs asynchronous jobs (Huey)

Important: the Werkzeug debugger started by `Procfile.dev` allows remote execution of Python 
commands. It should *not* be run in production. Also, the Web server started in the
development environment also doesn't require to run collectstatic.

Then go to:

* User interface: [http://localhost:5000/](http://localhost:2000/)
* API: [http://localhost:5000/api/](http://localhost:2000/api/)
* Admin: [http://localhost:5000/admin/](http://localhost:2000/admin/)


Debug
-----

To access the console, you can use `shell_plus`:

```
$ honcho run ./manage.py shell_plus

Python 3.4.3 (default, Mar 26 2015, 22:03:40)
Type "copyright", "credits" or "license" for more information.

IPython 3.1.0 -- An enhanced Interactive Python.
?         -> Introduction and overview of IPython's features.
%quickref -> Quick reference.
help      -> Python's own help system.
object?   -> Details about 'object', use 'object??' for extra details.

In [1]: from instance.tasks import provision_sandbox_instance

In [2]: result = provision_sandbox_instance(
    sub_domain='badges.sandbox',
    name='Badges',
    s3_access_key='XXX',
    s3_secret_access_key='XXX',
    s3_bucket_name='sandbox-edxapp-storage',
)
```
