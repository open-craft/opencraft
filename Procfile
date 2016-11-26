web: gunicorn opencraft.wsgi --timeout 60 --workers 4 --log-file -
websocket: python3 websocket.py
worker: python3 manage.py run_huey --no-periodic
periodic: python3 manage.py run_huey --workers=0
