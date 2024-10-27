# app/messages/soil_moisture_request_message.py

import json
import uuid
from datetime import datetime

class SoilMoistureRequestMessage:
    def __init__(self, rq_mqtt_topic = "control/soil-moisture/", rs_mqtt_topic = "status/soil-moisture/",  request_id = None, method_name="get-soil-moisture", sensor_id = 0, 
                 create_date = None, additional_info = None):
        self.rq_mqtt_topic = rq_mqtt_topic
        self.rs_mqtt_topic = rs_mqtt_topic
        self.request_id = request_id or str(uuid.uuid4())
        self.method_name = method_name
        self.sensor_id = sensor_id
        self.create_date = create_date or datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            "RqMqttTopic": self.rq_mqtt_topic, 
            "RsMqttTopic": self.rs_mqtt_topic,
            "RequestId": self.request_id,
            "MethodName": self.method_name,
            "SensorId": self.sensor_id,
            "CreateDate": self.create_date
        }

    def to_json(self):
        return json.dumps(self.to_dict())
