# app/gui/mqtt_subscriber.py

from app.mqtt.mqtt_client import MQTTClient
import logging

class MQTTSubscriber:
    def __init__(self, broker_address, topic, on_data_received):
        """
        broker_address : str
            MQTT broker address.
        topic : str
            The MQTT topic to subscribe to.
        on_data_received : callable
            A callback function that accepts one parameter (the data).
        """
        self.mqtt_client = MQTTClient(broker_address=broker_address, topic=topic)
        self.mqtt_client.on_message_callback = on_data_received

    def start(self):
        self.mqtt_client.start()

    def stop(self):
        self.mqtt_client.stop()
