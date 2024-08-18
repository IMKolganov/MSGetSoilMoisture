# app/routes/index.py

from flask import jsonify
from . import bp

@bp.route('/')
def index():
    return jsonify({'message': 'Welcome to the Soil Moinsture Service'}), 200
