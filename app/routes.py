from flask import Blueprint, request, jsonify
import requests
import random
from .utils import fetch_webservice_data

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET'])
def index():
    return jsonify({'service': 'Microservice GetSoilMoisture'}), 200

@main_bp.route('/get-soil-moisture', methods=['GET'])
def get_soil_moisture():
    is_dev = request.args.get('isDev') == '1'
    
    if is_dev:
        # Генерация случайных данных для режима разработки
        random_data = {
            'webservice_data': {
                'soil_moisture': round(random.uniform(-20.0, 40.0), 2),
            }
        }
        return jsonify(random_data), 200
    
    try:
        data = fetch_webservice_data()
    except requests.RequestException as e:
        return jsonify({'error': str(e)}), 500

    result = {
        'webservice_data': data,
    }
    return jsonify(result), 200

@main_bp.route('/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({'status': 'ok'}), 200
