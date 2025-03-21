import pyvisa
from ThorlabsPM100 import ThorlabsPM100
from unittest.mock import MagicMock
from app.devices.mock_devices import MockThorlabsPM100

class ThorlabsDevice:
    # Class variable to track all connected devices
    _connected_devices = {}
    
    @classmethod
    def list_available_devices(cls):
        """List all available Thorlabs power meter devices"""
        devices = []
        try:
            rm = pyvisa.ResourceManager()
            resources = rm.list_resources()
            
            for res in resources:
                if "USB" in res and "0x1313" in res:  # Thorlabs vendor ID
                    try:
                        inst = rm.open_resource(res)
                        idn = inst.query("*IDN?").strip().split(',')
                        devices.append({
                            "resource": res,
                            "manufacturer": idn[0],
                            "model": idn[1],
                            "serial": idn[2],
                            "firmware": idn[3]
                        })
                        inst.close()
                    except Exception as e:
                        print(f"Error inspecting {res}: {e}")
            
            return devices
        except Exception as e:
            print(f"Error listing devices: {e}")
            return []
    
    @classmethod
    def get_device(cls, serial=None, resource=None, config=None):
        """Factory method to get a device by serial number or resource name"""
        # If we already have this device connected, return the existing instance
        device_key = serial or resource
        if device_key in cls._connected_devices:
            return cls._connected_devices[device_key]
        
        # Create a new device instance
        device = ThorlabsDevice(config=config)
        
        # Connect to the specific device
        if device.connect(serial=serial, resource=resource):
            cls._connected_devices[device_key] = device
            return device
        return None
    
    def __init__(self, config=None):
        self.rm = None
        self.inst = None
        self.device = None
        self.params = {}
        self.config = config if config is not None else {}
        self.wavelength = self.config.get("wavelength", 1550)  # Default 1550 nm
        self.resource = None
        self.serial = None
    
    def find_device(self, serial=None, resource=None):
        """Find a specific device by serial number or resource name"""
        try:
            self.rm = pyvisa.ResourceManager()
            resources = self.rm.list_resources()
            
            # If resource is specified, try to connect directly
            if resource and resource in resources:
                return self._try_connect(resource)
            
            # Otherwise, scan for devices
            for res in resources:
                if "USB" in res and "0x1313" in res:  # Thorlabs vendor ID
                    # If we're looking for a specific serial number, check it
                    if serial:
                        try:
                            inst = self.rm.open_resource(res)
                            idn = inst.query("*IDN?").strip().split(',')
                            device_serial = idn[2]
                            inst.close()
                            
                            if device_serial == serial:
                                return self._try_connect(res)
                        except Exception:
                            continue
                    else:
                        # No specific device requested, use the first one found
                        return self._try_connect(res)
            
            print(f"No matching Thorlabs Power Meter found. {'Serial: ' + serial if serial else ''}")
            return False
        
        except Exception as e:
            print(f"VISA resource error: {e}")
            return False
    
    def _try_connect(self, resource):
        """Try to connect to a specific resource"""
        try:
            print(f"Trying to connect to {resource}...")
            self.inst = self.rm.open_resource(resource)
            self.device = ThorlabsPM100(self.inst)
            
            # Get identification using raw VISA command
            idn = self.inst.query("*IDN?").strip().split(',')
            self.params = {
                "Manufacturer": idn[0],
                "Model": idn[1],
                "Serial": idn[2],
                "Firmware": idn[3],
                "Wavelength": f"{self.device.sense.correction.wavelength} nm",
                "Power Range": f"{self.device.sense.power.dc.range.upper} W"
            }
            
            # Store the serial and resource for future reference
            self.serial = idn[2]
            self.resource = resource
            
            # Configure measurement type to POWER
            self.device.sense.function = 'POWER'
            
            # Apply wavelength config
            self.device.sense.correction.wavelength = self.wavelength
            
            print(f"Connected to {self.params['Model']} at {resource}")
            return True
        
        except Exception as e:
            print(f"Failed to connect to {resource}: {e}")
            return False
    
    def connect(self, serial=None, resource=None):
        """Connect to a device by serial number or resource name"""
        if self.find_device(serial, resource):
            print(f"Connected to {self.params['Model']} (SN: {self.params['Serial']})")
            print(f"Current wavelength: {self.params['Wavelength']}")
            return True
        else:
            print("Using mock device")
            self.device = MockThorlabsPM100(MagicMock())
            self.params = {
                "Manufacturer": "MockThorlabs",
                "Model": "PM100D-MOCK",
                "Serial": serial or "MOCK1234",
                "Firmware": "1.0.0",
                "Wavelength": f"{self.wavelength} nm",
                "Power Range": "100 mW"
            }
            self.serial = serial or "MOCK1234"
            self.resource = resource or "MOCK_RESOURCE"
            return True
    
    def read_power(self):
        """Get power reading in mW"""
        if self.device:
            try:
                return self.device.read * 1000  # Convert W to mW
            except AttributeError:
                return self.device.power * 1000
        return 0.0
    
    def set_wavelength(self, wavelength):
        """Set measurement wavelength (300-1100nm or 800-1700nm depending on sensor)"""
        if self.device:
            try:
                self.device.sense.correction.wavelength = wavelength
                self.wavelength = wavelength
                self.params["Wavelength"] = f"{wavelength} nm"
                print(f"Wavelength updated to {wavelength} nm")
            except Exception as e:
                print(f"Wavelength setting error: {e}")
    
    def show_status(self):
        """Display device status"""
        if self.device:
            print(f"Device: {self.params['Model']} (SN: {self.params['Serial']})")
            print(f"Wavelength: {self.params['Wavelength']}")
            print(f"Current power: {self.read_power():.6f} mW")
    
    def disconnect(self):
        """Safely close connection to device"""
        if self.inst:
            try:
                self.inst.close()
                print(f"Disconnected from Thorlabs device {self.params['Serial']}")
                # Remove from connected devices
                if self.serial in self._connected_devices:
                    del self._connected_devices[self.serial]
                if self.resource in self._connected_devices:
                    del self._connected_devices[self.resource]
            except Exception as e:
                print(f"Error closing connection: {e}")
            finally:
                self.inst = None
                self.device = None
        else:
            print("No Thorlabs device to disconnect")
