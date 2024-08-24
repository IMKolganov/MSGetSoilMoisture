# app/services/soil_moisture_service.py

import random
import json
import time
import uuid
import pika
from datetime import datetime

from app.messages.soil_moisture_request_message import SoilMoistureRequestMessage

class SoilMoistureService:
    def __init__(self, rabbitmq_client):
        self.rabbitmq_client = rabbitmq_client

    def handle_request(self, ch, method, properties, body, app):
        request_data = json.loads(body)
        method_name = request_data.get('MethodName')
        correlation_id = properties.correlation_id

        if method_name == 'get-soil-moisture':
            # If the request comes with the WithoutMSMicrocontrollerManager flag
            if request_data.get('WithoutMSMicrocontrollerManager'):
                soil_moisture_value = round(random.uniform(0, 100), 2)

                # Create response in the required format
                response_message = {
                    'RequestId': request_data.get('GUID', str(uuid.uuid4())),
                    'MethodName': method_name,
                    'SensorId': request_data.get('SensorId', 1),
                    'SoilMoistureLevel': soil_moisture_value,
                    'CreateDate': datetime.utcnow().isoformat()
                }

                ch.basic_publish(
                    exchange='',
                    routing_key=app.config['MSGETSOILMOISTURE_TO_BACKEND_RESPONSE_QUEUE'],
                    body=json.dumps(response_message),
                    properties=pika.BasicProperties(
                        correlation_id=correlation_id
                    )
                )

                ch.basic_ack(delivery_tag=method.delivery_tag)
                print(f"Handled 'get-soil-moisture' request without MSMicrocontrollerManager. Response sent to {app.config['MSGETSOILMOISTURE_TO_BACKEND_RESPONSE_QUEUE']}")
                return

            message = SoilMoistureRequestMessage(
                request_id=request_data.get('GUID'),
                method_name='get-soil-moisture',
                sensor_id=0,
                create_date=datetime.utcnow().isoformat(),
                additional_info={"request_origin": "MSGetSoilMoisture"}
            )
            # Send request to MSMicrocontrollerManager
            self.rabbitmq_client.send_message(
                queue_name=app.config['MSGETSOILMOISTURE_TO_MSMICROCONTROLLERMANAGER_REQUEST_QUEUE'],
                message=message,
                correlation_id=correlation_id,
                reply_to=app.config['MSMICROCONTROLLERMANAGER_TO_MSGETSOILMOISTURE_RESPONSE_QUEUE']
            )
            print(f"Request sent to MSMicrocontrollerManager. Waiting for response...")

            # Wait for a response from MSMicrocontrollerManager with a 5-second timeout
            try:
                soil_moisture_response = self.rabbitmq_client.receive_message(
                    queue_name=app.config['MSMICROCONTROLLERMANAGER_TO_MSGETSOILMOISTURE_RESPONSE_QUEUE'],
                    correlation_id=correlation_id,
                    timeout=5  # Timeout in seconds
                )

                if soil_moisture_response:
                    ch.basic_publish(
                        exchange='',
                        routing_key=app.config['MSGETSOILMOISTURE_TO_BACKEND_RESPONSE_QUEUE'],
                        body=json.dumps(soil_moisture_response),
                        properties=pika.BasicProperties(
                            correlation_id=correlation_id
                        )
                    )
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    print(f"Received response from MSMicrocontrollerManager. Response sent to {app.config['MSGETSOILMOISTURE_TO_BACKEND_RESPONSE_QUEUE']}")
                else:
                    # Timeout expired, message not processed
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    print(f"Timeout expired. No response from MSMicrocontrollerManager. Message not processed.")

            except Exception as e:
                print(f"Error while receiving message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                print(f"Message handling failed due to error: {e}")

        else:
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            print(f"Unhandled method '{method_name}'. Message nack'ed.")

    def start_listening(self, app):
        time.sleep(3)  # Delay for service readiness
        print("SoilMoistureService: Starting to process messages...")
        self.rabbitmq_client.start_queue_listener(
            queue_name=app.config['BACKEND_TO_MSGETSOILMOISTURE_REQUEST_QUEUE'],
            on_message_callback=lambda ch, method, properties, body: self.handle_request(ch, method, properties, body, app)
        )
        print("SoilMoistureService: Listening for messages...")
