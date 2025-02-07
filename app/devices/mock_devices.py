from app.imports import *

# Mock Qontrol Device
class MockQontrol:
    def __init__(self, serial_port_name=None, response_timeout=None):
        self.device_id = "QX-1234"
        self.firmware = "1.0.0"
        self.n_chs = 100  # Simulate 100 channels
        self.imax = [0] * self.n_chs
        self.i = [0] * self.n_chs

    def connect(self):
        print("MockQontrol: Connected successfully.")

    def close(self):
        print("MockQontrol: Connection closed.")
# Mock Thorlabs PM100D Power Meter
class MockThorlabsPM100:
    """Mock version of Thorlabs PM100D Power Meter for testing."""
    
    def __init__(self, inst=None):
        self.power = 0.123  # Simulated power reading
        self.connected = False

    def connect(self):
        """Simulates connecting to the power meter."""
        self.connected = True
        print("[Mock] Thorlabs PM100D connected.")

    def disconnect(self):
        """Simulates disconnecting the power meter."""
        self.connected = False
        print("[Mock] Thorlabs PM100D disconnected.")

    def read_power(self):
        """Simulated power reading."""
        if not self.connected:
            print("[Mock] Warning: Trying to read power while disconnected!")
        return self.power
