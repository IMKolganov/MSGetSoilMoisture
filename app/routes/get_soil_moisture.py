from flask import jsonify, request, current_app
from . import bp
import random
import pika
import json
import uuid

@bp.route('/get-soil-moisture')
def get_soil_moisture():
    # Проверка наличия параметра isDev в запросе
    is_dev = request.args.get('isDev', default='0') == '1'
    
    if is_dev:
        soil_moisture_value = round(random.uniform(0, 100), 2)
        return jsonify({'soilMoistureValue': soil_moisture_value})
    
    # Если не isDev, отправляем запрос в очередь и ждем ответа
    response = send_and_receive_message(
        request_queue=current_app.config['BACKEND_TO_MSGETSOILMOISTURE_REQUEST_QUEUE'],
        response_queue=current_app.config['MSGETSOILMOISTURE_TO_BACKEND_QUEUE'],
        message={"MethodName": "get-soil-moisture"}
    )
    
    if response is None:
        return jsonify({'error': 'Failed to retrieve soil moisture value'}), 500
    
    return jsonify({'soilMoistureValue': response['SoilMoistureLevel']})

def send_and_receive_message(request_queue, response_queue, message, timeout=10):
    connection, channel = get_rabbitmq_connection()
    correlation_id = str(uuid.uuid4())
    response = None

    def callback(ch, method, properties, body):
        if properties.correlation_id == correlation_id:
            nonlocal response
            response = json.loads(body)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            ch.stop_consuming()

    try:
        # Отправка сообщения в очередь
        channel.basic_publish(
            exchange='',
            routing_key=request_queue,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                correlation_id=correlation_id,
                reply_to=response_queue
            )
        )

        # Прослушивание очереди для получения ответа
        channel.basic_consume(
            queue=response_queue,
            on_message_callback=callback,
            auto_ack=False
        )

        channel.start_consuming()

    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()

    return response

def get_rabbitmq_connection():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=current_app.config['RABBITMQ_HOST'])
    )
    channel = connection.channel()
    return connection, channel