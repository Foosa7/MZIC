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


class MockDAQ:
    """
    Mock version of the DAQ class for testing when no physical DAQ is present.
    """

    def __init__(self, config=None):
        self.config = config if config is not None else {}
        self._is_connected = False
        # Give the mock a 'device_name' so it looks like the real one
        self.device_name = "MockDAQ"

    def connect(self, device_name=None):
        # Always "succeed" in connecting
        self._is_connected = True
        print(f"[MockDAQ] Connected (mock) to device_name='{device_name}'")
        return True

    def list_ai_channels(self):
        if not self._is_connected:
            print("[MockDAQ] Device not connected.")
            return []
        # Return some pretend channels
        return [f"{self.device_name}/ai{i}" for i in range(7)]

    def read_voltage(self, channels=None, samples_per_channel=10,
                     min_val=-10.0, max_val=10.0):
        """
        Returns a fixed set of voltage samples for a single mock channel.
        """
        if not self._is_connected:
            print("[MockDAQ] Device not connected.")
            return None

        # Default to our single channel if none specified
        if channels is None:
            channels = self.list_ai_channels()

        if not channels:
            print("[MockDAQ] No channels to read from.")
            return None

        # Return a fixed value for each sample, e.g., 0.0 volts
        readings = [0.0 for _ in range(samples_per_channel)]
        return readings

    def show_status(self):
        if not self._is_connected:
            print("[MockDAQ] No DAQ device is connected.")
        else:
            print(f"[MockDAQ] Device Name: {self.device_name}")
            print(f"[MockDAQ] AI Channels: {self.list_ai_channels()}")

    def disconnect(self):
        if self._is_connected:
            print(f"[MockDAQ] Disconnecting device: {self.device_name}")
            self._is_connected = False
            self.device_name = None
        else:
            print("[MockDAQ] No device to disconnect.")
