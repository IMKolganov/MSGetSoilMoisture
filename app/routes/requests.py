# app/routes/requests.py

import pika
import json
import random
import time
from flask import Blueprint, request, jsonify, current_app

bp = Blueprint('requests', __name__)

connection = None
channel = None

def get_rabbitmq_connection():
    """Creates a connection to RabbitMQ and returns a channel and connection."""
    for attempt in range(5):
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=current_app.config['RABBITMQ_HOST']))
            channel = connection.channel()
            channel.queue_declare(queue=current_app.config['REQUEST_QUEUE_NAME'], durable=False, exclusive=False, auto_delete=False)
            channel.queue_declare(queue=current_app.config['RESPONSE_QUEUE_NAME'], durable=False, exclusive=False, auto_delete=False)
            return connection, channel
        except pika.exceptions.AMQPConnectionError:
            print("Connection failed, retrying...")
            time.sleep(5) 
    raise RuntimeError("Failed to connect to RabbitMQ after several attempts")

def process_message(ch, method, properties, body):
    """Callback function for processing messages from a RabbitMQ queue."""
    request_data = json.loads(body)
    method_name = request_data.get('MethodName')
    correlation_id = properties.correlation_id

    print(f"Received message: {request_data} with CorrelationId: {correlation_id}")

    if method_name == 'get-soil-moisture':
        soilMoistureLevel = round(random.uniform(0, 100), 2)

        response_message = {
            'SoilMoistureLevel': soilMoistureLevel,
        }
        response_json = json.dumps(response_message)

        ch.basic_publish(
            exchange='',
            routing_key=current_app.config['RESPONSE_QUEUE_NAME'],
            body=response_json,
            properties=pika.BasicProperties(
                correlation_id=correlation_id
            )
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
    else:
        error_message = {'error': 'Unknown methodName'}
        response_json = json.dumps(error_message)

        ch.basic_publish(
            exchange='',
            routing_key=current_app.config['RESPONSE_QUEUE_NAME'],
            body=response_json,
            properties=pika.BasicProperties(
                correlation_id=correlation_id
            )
        )
        print(f"Unknown methodName: {method_name}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def start_processing(app):
    """Starts a queue listener to process messages with application context."""
    with app.app_context():
        time.sleep(3)
        connection, channel = get_rabbitmq_connection()
        channel.basic_consume(
            queue=current_app.config['REQUEST_QUEUE_NAME'],
            on_message_callback=process_message,
            auto_ack=False
        )

        print("Processing messages...")
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            print("Interrupted. Closing connection...")
            channel.stop_consuming()
        finally:
            if connection:
                connection.close()