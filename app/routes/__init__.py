# app/routes/__init__.py

from flask import Blueprint

bp = Blueprint('routes', __name__)

from . import get_soil_moisture, index, healthcheck