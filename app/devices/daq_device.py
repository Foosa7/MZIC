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
            print(f"[INFO][DAQ] Connected to: {self.device_name}")
            return True
        else:
            print("[INFO][DAQ] Failed to connect.")
            return False

    def list_ai_channels(self):
        """
        List analog input channels for the connected device.
        """
        if not self._is_connected:
            print("[INFO][DAQ] Device not connected.")
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
            print("[INFO][DAQ] Device not connected.")
            return None
        
        # If no channels specified, read from all
        if channels is None:
            channels = self.list_ai_channels()
        
        if not channels:
            print("[INFO][DAQ] No channels to read from.")
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
            
    def read_power(self, channels=None, samples_per_channel=10, sample_rate=1000, min_val=-10.0, max_val=10.0, unit="uW"):
        """
        Read voltage from specified channels and convert to power in the specified unit.
        
        Args:
            channels (list): List of channel names to read from
            samples_per_channel (int): Number of samples to take per channel
            sample_rate (float): Sampling rate in Hz
            min_val (float): Minimum voltage value
            max_val (float): Maximum voltage value
            unit (str): Power unit ('mW', 'uW', or 'W')
        
        Returns:
            list: Power readings in specified unit
        """
        with nidaqmx.Task() as task:
            # Add channels to the task
            for ch in channels:
                task.ai_channels.add_ai_voltage_chan(
                    physical_channel=ch,
                    min_val=min_val,
                    max_val=max_val
                )
            
            # Configure timing
            task.timing.cfg_samp_clk_timing(
                rate=sample_rate,
                sample_mode=nidaqmx.constants.AcquisitionType.FINITE,
                samps_per_chan=samples_per_channel
            )
            
            # Read voltage data
            voltages = task.read(number_of_samples_per_channel=samples_per_channel)
            
            # Convert to numpy array for easier processing
            voltages = np.array(voltages)
            
            # Average the samples for each channel
            if voltages.ndim == 2:
                voltages = np.mean(voltages, axis=1)
            else:
                voltages = [np.mean(voltages)]

        # Convert voltage to power using photodiode-specific calibration
        power_in_watts = []
        for i, ch in enumerate(channels):
            V = voltages[i]
            if "ai0" in ch.lower():  
                power = 3.8934e-04 * V #- 1.3769e-6  # PD1
            elif "ai1" in ch.lower():  
                power = 3.8853e-04 * V  #- 7.2653e-6 # PD2
            elif "ai2" in ch.lower(): 
                power = 3.7686e-04 * V  #- 4.1698e-5 # PD3
            elif "ai3" in ch.lower():  
                power = 4.0387e-04 * V  #+ 3.57e-7# PD4
            elif "ai4" in ch.lower():  
                power = 3.6247e-04 * V  #-2.37e-5# PD5
            elif "ai5" in ch.lower(): 
                power = 3.6618e-04 * V  #-3.57e-5# PD6
            elif "ai6" in ch.lower():  
                power = 3.7097e-04 * V  #-2.139e-5# PD7
            elif "ai7" in ch.lower():  
                power = 4.0287e-04 * V  #-2.216e-6# PD8

            else:
                # Fallback to default conversion
                power = V / (self.config.get('load_resistor', 4700) * 
                            self.config.get('responsivity', 1.07))
            power_in_watts.append(power)

        # Convert to the desired unit
        if unit == "mW":
            return [p * 1e3 for p in power_in_watts]
        elif unit == "uW":
            return [p * 1e6 for p in power_in_watts]
        elif unit == "W":
            return power_in_watts
        else:
            raise ValueError(f"[ERROR][DAQ] Unsupported unit: {unit}. Use 'mW', 'uW', or 'W'.")

    def show_status(self):
        """
        Print basic status information about the connected device.
        """
        if not self._is_connected:
            print("[INFO][DAQ] No device is connected.")
            return
        
        print(f"[INFO][DAQ] Device Name: {self.device_name}")
        channels = self.list_ai_channels()
        print(f"[INFO][DAQ] AI Channels: {channels}")

    def disconnect(self):
        """
        'Disconnect' the DAQ device. 
        (For NI-DAQ, we typically just close tasks, 
         but here we reset our connected state.)
        """
        if self._is_connected:
            print(f"[INFO][DAQ] Disconnecting device: {self.device_name}")
            # Mark not connected
            self._is_connected = False
            self.device_name = None
        else:
            print("[INFO][DAQ] No device to disconnect.")

    def clear_task(self):
        """
        Clear any existing DAQ tasks.
        Should be called after completing measurements to release hardware resources.
        """
        try:
            with nidaqmx.Task() as task:
                # Creating and closing an empty task helps clear any hanging tasks
                pass
            print("[INFO][DAQ] Task cleared successfully")
        except Exception as e:
            print(f"[WARNING][DAQ] Error clearing task: {e}")
