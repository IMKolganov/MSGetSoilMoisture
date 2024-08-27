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
        try:
            request_data = json.loads(body)
            print("SoilMoistureService: Recive message")
            print(f"SoilMoistureService: {request_data}")
            method_name = request_data.get('MethodName')
            correlation_id = properties.correlation_id
            request_id = request_data.get('RequestId')
            sensor_id = request_data.get('SensorId', 0)

            if method_name == 'get-soil-moisture':
                if request_data.get('WithoutMSMicrocontrollerManager'):
                    # If the request comes with the WithoutMSMicrocontrollerManager flag
                    self.send_request_without_ms_microcontroller_manager(app, ch, request_id, method_name, sensor_id, correlation_id, method)
                    return
                
                self.send_request_to_ms_microcontroller_manager(app, request_id, method_name, sensor_id, correlation_id)
                soil_moisture_response = self.recive_answer_from_ms_microcontroller_manager(app, correlation_id, ch, method)
                self.send_result_to_backend(app, ch, soil_moisture_response, correlation_id, method)

            else:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                print(f"SoilMoistureService: Unhandled method '{method_name}'. Message nack'ed.")
        except Exception as e:
            print(f"SoilMoistureService: Error while receiving message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            print(f"SoilMoistureService: Message handling failed due to error: {e}")

    def start_listening(self, app):
        time.sleep(3)  # Delay for service readiness
        print("SoilMoistureService: Starting to process messages...")
        self.rabbitmq_client.start_queue_listener(
            queue_name=app.config['BACKEND_TO_MSGETSOILMOISTURE_REQUEST_QUEUE'],
            on_message_callback=lambda ch, method, properties, body: self.handle_request(ch, method, properties, body, app)
        )
        print("SoilMoistureService: Listening for messages...")
    
    
    
    
    def send_request_to_ms_microcontroller_manager(self, app, request_id, method_name, sensor_id, correlation_id):
        message = SoilMoistureRequestMessage(
            request_id=request_id,
            method_name=method_name,
            sensor_id=sensor_id,
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
        print(f"SoilMoistureService: Request sent to MSMicrocontrollerManager.")

    def recive_answer_from_ms_microcontroller_manager(self, app, correlation_id, ch, method):
        print("SoilMoistureService: Waiting for response...")
        try:
            soil_moisture_response = self.rabbitmq_client.receive_message(
                queue_name=app.config['MSMICROCONTROLLERMANAGER_TO_MSGETSOILMOISTURE_RESPONSE_QUEUE'],
                correlation_id=correlation_id,
                timeout=5  # Timeout in seconds
            )

            if soil_moisture_response:
                return soil_moisture_response
        
            else:
                # Timeout expired, message not processed
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                print(f"Timeout expired. No response from MSMicrocontrollerManager. Message not processed.")

        except Exception as e:
            print(f"Fatal error: {e}")

    def send_result_to_backend(self, app, ch, soil_moisture_response, correlation_id, method):
        response_message = self.prepare_response(soil_moisture_response)

        ch.basic_publish(
            exchange='',
            routing_key=app.config['MSGETSOILMOISTURE_TO_BACKEND_RESPONSE_QUEUE'],
            body=json.dumps(response_message),
            properties=pika.BasicProperties(
                correlation_id=correlation_id
            )
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"SoilMoistureService: Received response from MSMicrocontrollerManager. Response sent to "
                +f"{app.config['MSGETSOILMOISTURE_TO_BACKEND_RESPONSE_QUEUE']}")
        print(json.dumps(response_message))
        
    def send_request_without_ms_microcontroller_manager(self, app, ch, request_id, 
                                                        method_name, sensor_id, correlation_id, method):
        soil_moisture_value = round(random.uniform(1024, 3024), 2)
        soil_moisture_response = {
            'RequestId': request_id,
            'MethodName': method_name,
            'SensorId': sensor_id,
            'SoilMoistureLevel': soil_moisture_value,
            'CreateDate': datetime.utcnow().isoformat(),
        }

        response_message = self.prepare_response(soil_moisture_response)
        
        ch.basic_publish(
            exchange='',
            routing_key=app.config['MSGETSOILMOISTURE_TO_BACKEND_RESPONSE_QUEUE'],
            body=json.dumps(response_message),
            properties=pika.BasicProperties(
                correlation_id=correlation_id
            )
        )

        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"SoilMoistureService: Handled 'get-soil-moisture' request without MSMicrocontrollerManager. "
                + f"Response sent to {app.config['MSGETSOILMOISTURE_TO_BACKEND_RESPONSE_QUEUE']}")
        print(f"SoilMoistureService: {json.dumps(response_message)}")
        return

    def prepare_response(self, soil_moisture_response):
        error_message = ""
        if (soil_moisture_response.get('SoilMoistureLevel') <= 0):
                error_message = f"The sensor is not connected. SensorId: {soil_moisture_response.get('SensorId')} "
        moisture_percent = self.calculate_soil_moisture_percent(1024, 3024, soil_moisture_response.get('SoilMoistureLevel'))
        return {
            'RequestId': soil_moisture_response.get('RequestId'),
            'MethodName': soil_moisture_response.get('MethodName'),
            'SensorId': soil_moisture_response.get('SensorId'),
            'SoilMoistureLevelPercent': moisture_percent,
            'CreateDate': datetime.utcnow().isoformat(),
            'ErrorMessage': error_message,
        }
    

    def calculate_soil_moisture_percent(self, min_value, max_value, sensor_value):
        # Ensure that sensor_value is within the bounds of min and max
        if sensor_value < min_value:
            sensor_value = min_value
        elif sensor_value > max_value:
            sensor_value = max_value
        
        # Calculate the moisture percentage
        moisture_percent = ((sensor_value - min_value) / (max_value - min_value)) * 100
        
        # Invert the percentage since soil moisture typically decreases as sensor readings increase
        moisture_percent = 100 - moisture_percent
        
        return moisture_percent