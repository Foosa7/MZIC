import platform
import pyvisa
from ThorlabsPM100 import ThorlabsPM100, USBTMC
from unittest.mock import MagicMock
from app.devices.mock_devices import MockThorlabsPM100

class ThorlabsDevice:
    _connected_devices = {}
    
    @classmethod
    def list_available_devices(cls):
        """List all available Thorlabs power meter devices"""
        devices = []
        system = platform.system()
        try:
            if system == 'Windows':
                rm = pyvisa.ResourceManager()
                resources = rm.list_resources()
                for res in resources:
                    if "USB" in res and "0x1313" in res:
                        try:
                            with rm.open_resource(res) as inst:
                                idn = inst.query("*IDN?").strip().split(',')
                                if idn[0].strip().lower() == 'thorlabs':
                                    devices.append({
                                        "resource": res,
                                        "manufacturer": idn[0],
                                        "model": idn[1],
                                        "serial": idn[2],
                                        "firmware": idn[3]
                                    })
                        except Exception as e:
                            print(f"Error inspecting {res}: {e}")
            
            elif system == 'Linux':
                import glob
                usbtmc_devices = glob.glob('/dev/usbtmc*')
                for dev_path in usbtmc_devices:
                    try:
                        inst = USBTMC(device=dev_path)
                        idn = inst.query("*IDN?").strip().split(',')
                        if idn[0].strip().lower() == 'thorlabs':
                            devices.append({
                                "resource": dev_path,
                                "manufacturer": idn[0],
                                "model": idn[1],
                                "serial": idn[2],
                                "firmware": idn[3]
                            })
                        inst.close()
                    except Exception as e:
                        print(f"Error inspecting {dev_path}: {e}")
            
            return devices
        
        except Exception as e:
            print(f"Error listing devices: {e}")
            return []
    
    @classmethod
    def get_device(cls, serial=None, resource=None, config=None):
        device_key = serial or resource
        if device_key in cls._connected_devices:
            return cls._connected_devices[device_key]
        
        device = ThorlabsDevice(config=config)
        if device.connect(serial=serial, resource=resource):
            cls._connected_devices[device_key] = device
            return device
        return None

    def __init__(self, config=None):
        self.inst = None
        self.device = None
        self.params = {}
        self.config = config or {}
        self.wavelength = self.config.get("wavelength", 1550)
        self.resource = None
        self.serial = None

    def connect(self, serial=None, resource=None):
        if self._find_device(serial, resource):
            print(f"Connected to {self.params['Model']} (SN: {self.params['Serial']})")
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

    def _find_device(self, serial=None, resource=None):
        system = platform.system()
        try:
            if system == 'Windows':
                return self._windows_find_device(serial, resource)
            elif system == 'Linux':
                return self._linux_find_device(serial, resource)
            else:
                print(f"Unsupported OS: {system}")
                return False
        except Exception as e:
            print(f"Error finding device: {e}")
            return False

    def _windows_find_device(self, serial, resource):
        rm = pyvisa.ResourceManager()
        if resource:
            return self._try_connect_windows(resource, rm, serial)
        
        resources = rm.list_resources()
        for res in resources:
            if "USB" in res and "0x1313" in res:
                try:
                    with rm.open_resource(res) as inst:
                        idn = inst.query("*IDN?").strip().split(',')
                        if (not serial) or (idn[2] == serial):
                            return self._try_connect_windows(res, rm, serial)
                except Exception:
                    continue
        return False

    def _linux_find_device(self, serial, resource):
        import glob
        if resource:
            return self._try_connect_linux(resource, serial)
        
        for dev_path in glob.glob('/dev/usbtmc*'):
            if self._try_connect_linux(dev_path, serial):
                return True
        return False

    def _try_connect_windows(self, resource, rm, expected_serial):
        try:
            self.inst = rm.open_resource(resource)
            idn = self.inst.query("*IDN?").strip().split(',')
            if expected_serial and idn[2] != expected_serial:
                self.inst.close()
                return False
            
            self._initialize_device(resource, idn)
            return True
        except Exception as e:
            print(f"Windows connection failed: {e}")
            return False

    def _try_connect_linux(self, resource, expected_serial):
        try:
            self.inst = USBTMC(device=resource)
            idn = self.inst.query("*IDN?").strip().split(',')
            if expected_serial and idn[2] != expected_serial:
                self.inst.close()
                return False
            
            self._initialize_device(resource, idn)
            return True
        except Exception as e:
            print(f"Linux connection failed: {e}")
            return False

    def _initialize_device(self, resource, idn):
        self.device = ThorlabsPM100(self.inst)
        self.params = {
            "Manufacturer": idn[0],
            "Model": idn[1],
            "Serial": idn[2],
            "Firmware": idn[3],
            "Wavelength": f"{self.device.sense.correction.wavelength} nm",
            "Power Range": f"{self.device.sense.power.dc.range.upper} W"
        }
        self.resource = resource
        self.serial = idn[2]
        self.device.sense.function = 'POWER'
        self.device.sense.correction.wavelength = self.wavelength
        print(f"Connected to {self.params['Model']} at {resource}")

    def read_power(self):
        if self.device:
            try:
                return self.device.read * 1000
            except AttributeError:
                return self.device.power * 1000
        return 0.0

    def set_wavelength(self, wavelength):
        if self.device:
            try:
                self.device.sense.correction.wavelength = wavelength
                self.wavelength = wavelength
                self.params["Wavelength"] = f"{wavelength} nm"
            except Exception as e:
                print(f"Wavelength setting error: {e}")

    def disconnect(self):
        if self.inst:
            try:
                self.inst.close()
                print(f"Disconnected from {self.params['Serial']}")
                ThorlabsDevice._connected_devices.pop(self.serial, None)
                ThorlabsDevice._connected_devices.pop(self.resource, None)
            except Exception as e:
                print(f"Error closing connection: {e}")
            finally:
                self.inst = None
                self.device = None

    # Remaining methods (show_status, etc.) remain unchanged
    def show_status(self):
        """Display device status"""
        if self.device:
            print(f"Device: {self.params['Model']} (SN: {self.params['Serial']})")
            print(f"Wavelength: {self.params['Wavelength']}")
            print(f"Current power: {self.read_power():.6f} mW")
    
    # def disconnect(self):
    #     """Safely close connection to device"""
    #     if self.inst:
    #         try:
    #             self.inst.close()
    #             print(f"Disconnected from Thorlabs device {self.params['Serial']}")
    #             # Remove from connected devices
    #             if self.serial in self._connected_devices:
    #                 del self._connected_devices[self.serial]
    #             if self.resource in self._connected_devices:
    #                 del self._connected_devices[self.resource]
    #         except Exception as e:
    #             print(f"Error closing connection: {e}")
    #         finally:
    #             self.inst = None
    #             self.device = None
    #     else:
    #         print("No active connection to disconnect")
