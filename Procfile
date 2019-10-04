web: gunicorn opencraft.wsgi --timeout 60 --workers 4 --log-file -
websocket: daphne -p 2001 opencraft.asgi:application
worker: python3 manage.py run_huey --no-periodic
worker_low_priority: HUEY_QUEUE_NAME=opencraft_low_priority python3 manage.py run_huey --no-periodic
periodic: python3 manage.py run_huey --workers=0
