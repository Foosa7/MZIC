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


# Mock NI-DAQ Device
class MockNIDAQ:
    """Mock version of National Instruments DAQ for testing."""
    
    def __init__(self, serial_port_name=None, response_timeout=None):
        self.device_id = "NI-DAQ-5678"
        self.firmware = "2.1.0"
        self.n_chs = 16  # Simulating 16 channels for the mock device
        self.sample_rate = 1000  # Simulated sample rate (Hz)
        self.channels = {f"Ch{i+1}": {"voltage": 0.0, "current": 0.0} for i in range(self.n_chs)}
        self.connected = False
    
    def connect(self):
        """Simulates connecting to the NI-DAQ device."""
        self.connected = True
        print("MockNI-DAQ: Connected successfully.")

    def disconnect(self):
        """Simulates disconnecting the NI-DAQ device."""
        self.connected = False
        print("MockNI-DAQ: Connection closed.")
    
    def read_channel(self, channel):
        """Simulates reading a channel's voltage and current."""
        if not self.connected:
            print("[Mock] Error: Device is not connected!")
            return None
        if channel not in self.channels:
            print(f"[Mock] Error: Channel {channel} does not exist!")
            return None
        
        voltage = self.channels[channel]["voltage"]
        current = self.channels[channel]["current"]
        print(f"[Mock] Channel {channel} - Voltage: {voltage} V, Current: {current} A")
        return voltage, current
    
    def simulate_channel_reading(self, channel, voltage=None, current=None):
        """Simulates manually setting values for a channel's readings."""
        if channel not in self.channels:
            print(f"[Mock] Error: Channel {channel} does not exist!")
            return
        
        if voltage is not None:
            self.channels[channel]["voltage"] = voltage
        if current is not None:
            self.channels[channel]["current"] = current
        
        print(f"[Mock] Channel {channel} simulated values - Voltage: {voltage} V, Current: {current} A")

    def get_sample_rate(self):
        """Returns the sample rate of the device."""
        return self.sample_rate

    def set_sample_rate(self, sample_rate):
        """Sets the sample rate of the device."""
        self.sample_rate = sample_rate
        print(f"[Mock] Sample rate set to: {sample_rate} Hz")
