# pi_publisher.py

import time
import logging
from app.devices.qontrol_device import QontrolDevice
from app.devices.thorlabs_device import ThorlabsDevice
from app.mqtt.mqtt_client import MQTTClient

# (Optionally) Configure logging
logging.basicConfig(level=logging.INFO)

def get_device_data():
    """
    Read data from the devices.  
    (Assumes that your device modules have a method like .read_data().)
    """
    # Instantiate device objects (you may already have singleton instances or another method)
    qontrol = QontrolDevice()
    thorlabs = ThorlabsDevice()
    
    data = {
        "qontrol": qontrol.read_data(),
        "thorlabs": thorlabs.read_data()
    }
    return data

def main():
    # Replace with your MQTT broker’s address (e.g., the Windows PC’s IP or a central broker)
    mqtt_broker = "192.168.1.100"  
    mqtt_topic = "device/data"
    
    mqtt_client = MQTTClient(broker_address=mqtt_broker, topic=mqtt_topic)
    mqtt_client.start()

    try:
        while True:
            data = get_device_data()
            logging.info("Publishing data: %s", data)
            mqtt_client.publish(data)
            time.sleep(1)  # Publish every second (adjust as needed)
    except KeyboardInterrupt:
        logging.info("Stopping MQTT publisher...")
    finally:
        mqtt_client.stop()

if __name__ == '__main__':
    main()
