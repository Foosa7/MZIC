# app/mqtt/mqtt_client.py

import json
import logging
import paho.mqtt.client as mqtt

class MQTTClient:
    def __init__(self, broker_address, broker_port=1883, topic="device/data", client_id="", username=None, password=None):
        """
        broker_address : str
            The IP address or hostname of the MQTT broker.
        broker_port : int
            The port number (default is 1883).
        topic : str
            The topic to subscribe to or publish on.
        client_id : str
            A unique client identifier.
        username, password : str (optional)
            If your broker requires authentication.
        """
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.topic = topic
        self.client = mqtt.Client(client_id)
        if username and password:
            self.client.username_pw_set(username, password)
        # Set callback functions
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        # This callback is set by the user to handle received messages
        self.on_message_callback = None

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logging.info("Connected to MQTT Broker at %s:%s", self.broker_address, self.broker_port)
            # Automatically subscribe to the topic after connecting
            client.subscribe(self.topic)
        else:
            logging.error("Failed to connect, return code %d", rc)

    def on_message(self, client, userdata, msg):
        logging.info("Received message from topic %s: %s", msg.topic, msg.payload)
        if self.on_message_callback:
            try:
                # Assuming messages are in JSON format
                payload = json.loads(msg.payload.decode())
            except json.JSONDecodeError:
                payload = msg.payload.decode()
            self.on_message_callback(payload)

    def start(self):
        """Connect to the broker and start the network loop in a background thread."""
        self.client.connect(self.broker_address, self.broker_port)
        self.client.loop_start()

    def stop(self):
        """Stop the network loop and disconnect from the broker."""
        self.client.loop_stop()
        self.client.disconnect()

    def publish(self, data):
        """
        Publish data to the MQTT topic.
        
        data : dict or any JSON-serializable object
        """
        payload = json.dumps(data)
        result = self.client.publish(self.topic, payload)
        status = result[0]
        if status == 0:
            logging.info("Sent message to topic %s", self.topic)
        else:
            logging.error("Failed to send message to topic %s", self.topic)
