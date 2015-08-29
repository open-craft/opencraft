web: gunicorn opencraft.wsgi --log-file -
websocket: ./websocket.py
worker: ./manage.py run_huey --no-periodic
periodic: ./manage.py run_huey
