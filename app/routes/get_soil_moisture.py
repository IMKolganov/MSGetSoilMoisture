# app/routes/get_soil_moisture.py

from flask import jsonify
from . import bp
import random

@bp.route('/get-soil-moisture')
def get_temperature_and_humidify():
    soilMoistureValue = round(random.uniform(0, 100), 2)
    
    response_message = {
        'soilMoistureValue': soilMoistureValue,
    }
    
    return jsonify(response_message)