# app/config.py

import os

class Config:
    RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
    REQUEST_QUEUE_NAME = os.getenv('REQUEST_QUEUE_NAME', 'soilMoistureRequestQueue')
    RESPONSE_QUEUE_NAME = os.getenv('RESPONSE_QUEUE_NAME', 'soilMoistureResponseQueue')
    MICROCONTROLLER_MANAGER_URL = os.getenv('MICROCONTROLLER_MANAGER_URL', 'http://localhost:4000')

class DevelopmentConfig(Config):
    DEBUG = True
    RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
    REQUEST_QUEUE_NAME = os.getenv('REQUEST_QUEUE_NAME', 'soilMoistureRequestQueue')
    RESPONSE_QUEUE_NAME = os.getenv('RESPONSE_QUEUE_NAME', 'soilMoistureResponseQueue')
    MICROCONTROLLER_MANAGER_URL = os.getenv('MICROCONTROLLER_MANAGER_URL', 'http://localhost:4000')

class DockerConfig(Config):
    RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
    REQUEST_QUEUE_NAME = os.getenv('REQUEST_QUEUE_NAME', 'soilMoistureRequestQueue')
    RESPONSE_QUEUE_NAME = os.getenv('RESPONSE_QUEUE_NAME', 'soilMoistureResponseQueue')
    MICROCONTROLLER_MANAGER_URL = os.getenv('MICROCONTROLLER_MANAGER_URL', 'http://microcontroller_manager:4000')
