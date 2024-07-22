import requests
from flask import current_app

def fetch_webservice_data():
    webservice_url = current_app.config['MICROCONTROLLER_MANAGER_URL']
    response = requests.get(webservice_url)
    response.raise_for_status()
    return response.json()
