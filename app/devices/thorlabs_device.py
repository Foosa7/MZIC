import pyvisa
from ThorlabsPM100 import ThorlabsPM100
from unittest.mock import MagicMock
from app.devices.mock_devices import MockThorlabsPM100

class ThorlabsDevice:
    def __init__(self, config=None):
        self.rm = None
        self.inst = None
        self.device = None
        self.params = {}
        self.config = config if config is not None else {}
        self.wavelength = self.config.get("wavelength", 1550)  # Default 1550 nm

    def find_device(self):
        try:
            self.rm = pyvisa.ResourceManager()
            resources = self.rm.list_resources()
            print(f"Available VISA resources: {resources}")

            for res in resources:
                if "USB" in res and "0x1313" in res:  # Thorlabs vendor ID
                    try:
                        print(f"Trying to connect to {res}...")
                        self.inst = self.rm.open_resource(res)
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

                        # Configure measurement type to POWER
                        self.device.sense.function = 'POWER'
                        
                        # Apply wavelength config
                        self.device.sense.correction.wavelength = self.wavelength
                        
                        print(f"Connected to {self.params['Model']} at {res}")
                        return True

                    except Exception as e:
                        print(f"Failed to connect to {res}: {e}")
                        continue

            print("No Thorlabs Power Meter found.")
            return False

        except Exception as e:
            print(f"VISA resource error: {e}")
            return False

    def connect(self):
        if self.find_device():
            print(f"Connected to {self.params['Model']} (SN: {self.params['Serial']})")
            print(f"Current wavelength: {self.params['Wavelength']}")
        else:
            print("Using mock device")
            self.device = MockThorlabsPM100(MagicMock())
            self.params = {
                "Manufacturer": "MockThorlabs",
                "Model": "PM100D-MOCK",
                "Serial": "MOCK1234",
                "Firmware": "1.0.0",
                "Wavelength": f"{self.wavelength} nm",
                "Power Range": "100 mW"
            }

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

    def disconnect(self):
        """Safely close connection to device"""
        if self.inst:
            try:
                self.inst.close()
                print("Disconnected from Thorlabs device")
            except Exception as e:
                print(f"Error closing connection: {e}")
            finally:
                self.inst = None
                self.device = None
        else:
            print("No active connection to disconnect")


# For testing
if __name__ == "__main__":
    config = {"wavelength": 1550}
    thorlabs = ThorlabsDevice(config)
    thorlabs.connect()
    
    if thorlabs.device:
        thorlabs.show_status()
        thorlabs.set_wavelength(1310)
        thorlabs.show_status()
    
    thorlabs.disconnect()
