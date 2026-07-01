import requests


def fetch(url: str):
    response = requests.get(url, timeout=5)
    return response.json()
