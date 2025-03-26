# app/devices/daq_device.py
from app.imports import *

class DAQ:
    """
    Class representing an NI DAQ device (e.g., USB-6000).
    Manages discovery, connection, reading data, and disconnection.
    """

    # Class variable to track all connected DAQ devices by name
    _connected_devices = {}

    @classmethod
    def list_available_devices(cls):
        """
        Return a list of available NI DAQ devices (dicts with 'name' and 'product_type').
        """
        system = System.local()
        devices_info = []
        for dev in system.devices:
            devices_info.append({
                "name": dev.name,
                "product_type": dev.product_type
            })
        return devices_info

    @classmethod
    def get_device(cls, device_name=None, config=None):
        """
        Factory method to get a DAQ by device_name.
        If already connected, returns the existing instance.
        Otherwise, creates a new instance and connects it.
        
        :param device_name: The NI-DAQ device name (e.g., 'Dev1') you want to connect to.
                            If None, tries to find the first USB-6000 device automatically.
        :param config: Optional dict for extra configuration (ranges, etc.).
        :return: A DAQ instance or None if no suitable device is found.
        """
        # Use the device_name as a key in our connected_devices dictionary
        device_key = device_name or "AUTO_USB_6000"

        if device_key in cls._connected_devices:
            return cls._connected_devices[device_key]

        # Create a new device instance
        device = DAQ(config=config)

        # Attempt to connect
        if device.connect(device_name=device_name):
            cls._connected_devices[device_key] = device
            return device

        return None

    def __init__(self, config=None):
        """
        Initialize a DAQ instance with optional config.
        """
        self.config = config if config is not None else {}
        self.system = System.local()
        self.device_name = None
        self._is_connected = False

    def find_device(self, device_name=None):
        """
        Find a specific device by name (e.g., 'Dev1'). If device_name is None,
        automatically search for the first 'USB-6000'.
        
        :return: True if found, else False
        """
        if device_name:
            # Check if the named device actually exists
            for dev in self.system.devices:
                if dev.name == device_name:
                    self.device_name = device_name
                    return True
            return False
        else:
            # Auto-find the first USB-6000
            for dev in self.system.devices:
                if dev.product_type == "USB-6000":
                    self.device_name = dev.name
                    return True
            return False

    def connect(self, device_name=None):
        """
        Connect to the DAQ device. If device_name is None, attempts to find a USB-6000.
        
        :return: True if connected successfully, False otherwise.
        """
        if self.find_device(device_name=device_name):
            self._is_connected = True
            print(f"Connected to DAQ device: {self.device_name}")
            return True
        else:
            print("Failed to connect to a DAQ device.")
            return False

    def list_ai_channels(self):
        """
        List analog input channels for the connected device.
        """
        if not self._is_connected:
            print("Device not connected.")
            return []
        
        for dev in self.system.devices:
            if dev.name == self.device_name:
                return [chan.name for chan in dev.ai_physical_chans]
        return []

    def read_voltage(self, channels=None, samples_per_channel=10, min_val=-10.0, max_val=10.0):
        """
        Read multiple samples (software-timed) from specified channels.
        
        :param channels: A list of channel names, e.g. ['Dev1/ai0', 'Dev1/ai2'].
                         If None, read from all available AI channels on the device.
        :param samples_per_channel: Number of samples to read for each channel.
        :param min_val: Minimum expected voltage
        :param max_val: Maximum expected voltage
        :return: A list of lists if multiple channels, or just a list if one channel.
        """
        if not self._is_connected:
            print("Device not connected.")
            return None
        
        # If no channels specified, read from all
        if channels is None:
            channels = self.list_ai_channels()
        
        if not channels:
            print("No channels to read from.")
            return None

        data = None
        with nidaqmx.Task() as task:
            # Add channels to the task
            for ch in channels:
                task.ai_channels.add_ai_voltage_chan(
                    physical_channel=ch,
                    min_val=min_val,
                    max_val=max_val
                )
            # Gather raw data
            data = task.read(number_of_samples_per_channel=samples_per_channel)
        
        # Average raw data
        if isinstance(data, list):
            arr = np.array(data)
            if arr.ndim == 2:
                # Multiple channels
                return arr.mean(axis=1).tolist()
            elif arr.ndim == 1:
                # Single channel
                return float(arr.mean())

        return data
    
    def read_power_in_mW(self, channels=None, samples_per_channel=10, min_val=-10.0, max_val=10.0, load_resistor=50, responsivity=1.07):
        """
        Read voltage from specified channels and convert to power in mW.

        Conversion:
            P_in (mW) = (1000 * V_out) / (load_resistor * responsivity)

        :param channels: A list of channel names, e.g. ['Dev1/ai0', 'Dev1/ai2'].
                        If None, read from all available AI channels on the device.
        :param samples_per_channel: Number of samples to read for each channel.
        :param min_val: Minimum expected voltage.
        :param max_val: Maximum expected voltage.
        :param load_resistor: The terminating resistor value in ohms (default 50 Ω).
        :param responsivity: Photodiode responsivity in A/W (default 1.07 A/W for 1550 nm).
        :return: A list of power values in mW.
        """
        voltages = self.read_voltage(
            channels=channels,
            samples_per_channel=samples_per_channel,
            min_val=min_val,
            max_val=max_val
        )
        
        if voltages is None:
            return None
        
        # Convert the measured voltage to power in mW.
        # The photodiode generates a photocurrent I = P_in * responsivity.
        # That current flowing through the load resistor gives V_out = I * load_resistor.
        # Rearranging gives:
        #     P_in = V_out / (load_resistor * responsivity)
        # Multiply by 1000 to convert watts to mW.
        return [1000.0 * v / (load_resistor * responsivity) for v in voltages]
        
        

    def show_status(self):
        """
        Print basic status information about the connected device.
        """
        if not self._is_connected:
            print("No DAQ device is connected.")
            return
        
        print(f"DAQ Device Name: {self.device_name}")
        channels = self.list_ai_channels()
        print(f"AI Channels: {channels}")

    def disconnect(self):
        """
        'Disconnect' the DAQ device. 
        (For NI-DAQ, we typically just close tasks, 
         but here we reset our connected state.)
        """
        if self._is_connected:
            print(f"Disconnecting DAQ device: {self.device_name}")
            # Mark not connected
            self._is_connected = False
            self.device_name = None
        else:
            print("No DAQ device to disconnect.")
