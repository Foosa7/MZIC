
import pyvisa
from ThorlabsPM100 import ThorlabsPM100
from unittest.mock import MagicMock
from app.devices.mock_devices import MockThorlabsPM100

class ThorlabsDevice:
    def __init__(self):
        self.rm = None
        self.inst = None
        self.device = None

    def find_device(self):
        """Automatically find the Thorlabs Power Meter."""
        try:
            self.rm = pyvisa.ResourceManager()
            resources = self.rm.list_resources()
            print(f"Available VISA resources: {resources}")

            for res in resources:
                if "USB" in res:  # Look for USB-based connections
                    try:
                        print(f"Trying to connect to {res}...")
                        self.inst = self.rm.open_resource(res)
                        self.device = ThorlabsPM100(self.inst)
                        print(f"Connected to Thorlabs Power Meter at {res}")
                        return True
                    except Exception as e:
                        print(f"Failed to connect to {res}: {e}")
                        continue

            print("No Thorlabs Power Meter found.")
            return False

        except Exception as e:
            print(f"Error accessing VISA resources: {e}")
            return False

    def connect(self):
        """Connect to the Thorlabs power meter automatically."""
        if self.find_device():
            print("Thorlabs Power Meter connected successfully.")
        else:
            print("Using Mock Thorlabs Power Meter instead.")
            self.device = MockThorlabsPM100(MagicMock())  # Use mock device

    def disconnect(self):
        """Disconnect the Thorlabs device."""
        if self.device:
            print("Thorlabs Power Meter disconnected.")
            if self.inst:
                self.inst.close()
        else:
            print("No Thorlabs device to disconnect.")

# For testing
if __name__ == "__main__":
    thorlabs = ThorlabsDevice()
    thorlabs.connect()
    print(f"Power Reading: {thorlabs.device.read_power()} mW")
    thorlabs.disconnect()
