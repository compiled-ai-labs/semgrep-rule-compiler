import requests


def fetch(url: str):
    response = requests.get(url)
    return response.json()
