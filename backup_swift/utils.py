
import requests


def ping_heartbeat_url(url):
    try:
        response = requests.get(url, timeout=30)
        return 200 <= response.status_code < 300
    except requests.RequestException as e:
        return False