# app/devices/qontrol_device.py

from app.imports import *

class QontrolDevice:
    def __init__(self, config=None):
        self.device = None
        self.serial_port = None
        self.params = {}

        # Store the entire config so we can reference it anywhere
        self.config = config if config is not None else {}

        # Alternatively, store specific values from config
        self.globalcurrrentlimit = self.config.get("globalcurrrentlimit", 5.0)  # default=5.0 if config not found


    def find_serial_port(self):
        """Find the Qontrol device by scanning available COM ports, prioritizing FTDI."""
        print("\nScanning available COM ports for Qontrol Device...")

        # Get available ports and sort in reverse order (search last COM ports first)
        available_ports = list(serial.tools.list_ports.comports())
        available_ports.sort(key=lambda port: port.device, reverse=True)

        if not available_ports:
            print("No available COM ports found.")
            return None

        print(f"Available ports: {[port.device for port in available_ports]}")

        for port in available_ports:
            # Filter for FTDI devices (Qontrol uses an FTDI chip)
            if "FTDI" not in port.manufacturer and "FT" not in port.description:
                continue  # Skip non-FTDI devices

            try:
                print(f"Trying to connect to {port.device} (FTDI detected)...")
                q = qontrol.QXOutput(serial_port_name=port.device, response_timeout=0.03)

                # If connection is successful, store device info
                self.serial_port = port.device
                self.device = q
                # print(f"Successfully connected to Qontrol Device on {port.device}")
                print ("Qontroller '{:}' initialised with firmware {:} and {:} channels".format(q.device_id, q.firmware, q.n_chs) )
                self.params = {
                    "Device id": q.device_id,
                    "Available channels": q.n_chs,
                    "Firmware": q.firmware,
                    "Available modes": int(q.n_chs / 8),
                }
                return port.device
                
            except Exception as e:
                print(f"Failed to connect on {port.device}: {e}")
                continue

        print("No Qontrol device found.")
        return None

    def connect(self):
        """Connect to the Qontrol device automatically."""
        if self.find_serial_port():
            # print(
            #     f"Qontroller '{self.device.device_id}' initialized with "
            #     f"{self.device.n_chs} channels."
            # )
            q = self.device
            print(f'Initialize current limit globally on all available channels ({q.n_chs}) to {self.globalcurrrentlimit} mA')
            for i in range(q.n_chs):
                q.imax[i] = self.globalcurrrentlimit
            print('')

        else:
            print("Qontrol device connection failed.")

    def disconnect(self):
        """Disconnect the Qontrol device."""
        if self.device:
            q = self.device
            for i in range(q.n_chs):
                q.i[i] = 0
                print(f"Resetting the current for channel {i} to 0 mA")

            self.device.close()
            print("Qontrol device disconnected.")
            
        else:
            print("No Qontrol device to disconnect.")

    def set_current(self, channel, current):
        """Set the current for a specific channel."""
        self.device.i[int(channel)] = current
        print(f"Set current for channel {channel} to {current} mA")




# For testing
if __name__ == "__main__":
    qontrol_device = QontrolDevice()
    qontrol_device.connect()
    qontrol_device.disconnect()
