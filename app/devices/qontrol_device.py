# app/devices/qontrol_device.py

from app.imports import *
import platform  


class QontrolDevice:
    def __init__(self, config=None):
        """
        Initialize the QontrolDevice wrapper.
        
        config: Optional dictionary. For example, you may include
                {"globalcurrrentlimit": 5.0} (mA) if not otherwise set.
        """
        self.device = None
        self.serial_port = None
        self.params = {}
        self.config = config if config is not None else {}
        # Global current limit (in mA) to be set on all channels after connecting.
        self.globalcurrrentlimit = self.config.get("globalcurrrentlimit")

    def _enforce_operation_delay(self):
        """Ensure minimum time between operations"""
        elapsed = time.time() - self.last_operation_time
        if elapsed < self.operation_delay:
            time.sleep(self.operation_delay - elapsed)
        self.last_operation_time = time.time()


    def find_serial_port(self):
        """
        Scan available COM ports for a Qontrol device.
        Prioritize FTDI devices (which Qontrol uses).
        """
        print("\nScanning available COM ports for Qontrol Device...")
        available_ports = list(serial.tools.list_ports.comports())
        # Search the higher-numbered ports first.
        available_ports.sort(key=lambda port: port.device, reverse=True)

        if not available_ports:
            print("No available COM ports found.")
            return None

        print("Available ports:", [port.device for port in available_ports])

        for port in available_ports:
            # Linux-specific detection by VID/PID
            if platform.system() == "Linux":
                if not (port.vid == 0x0403 and port.pid == 0x6001):  # FTDI FT232
                    continue
                print(f"Trying {port.device} (FTDI detected by VID/PID 0403:6001)...")
            else:
                # Original detection for other OSes
                if ("FTDI" not in (port.manufacturer or "") and \
                   "FT" not in (port.description or "")):
                    continue
                print(f"Trying {port.device} (FTDI detected by description)...")

            try:
                # Instantiate a QXOutput from the core library.
                q = qontrol.QXOutput(serial_port_name=port.device, response_timeout=0.5)
                self.serial_port = port.device
                self.device = q

                print("Qontroller '{0}' initialized with firmware {1} and {2} channels."
                      .format(q.device_id, q.firmware, q.n_chs))
                self.params = {
                    "Device id": q.device_id,
                    "Available channels": q.n_chs,
                    "Firmware": q.firmware,
                    "Available modes": int(q.n_chs / 8)
                }
                return port.device

            except Exception as e:
                print(f"Failed to connect on {port.device}: {str(e)}")
                continue

        print("No Qontrol device found.")
        return None
        
    def connect(self):
        """
        Automatically scan for and connect to the Qontrol device.
        On success, sets the global current limit on all channels and
        displays device status.
        """
        if self.find_serial_port():
            q = self.device
            print("\nInitializing current limit on all channels ({0}) to {1} mA"
                  .format(q.n_chs, self.globalcurrrentlimit))
            for i in range(q.n_chs):
                q.imax[i] = self.globalcurrrentlimit
            print("\nDevice Status:")
            self.show_status()
        else:
            print("Qontrol device connection failed.")

    def disconnect(self):
        """
        Disconnect from the Qontrol device.
        Before disconnecting, reset all channel currents to 0 mA.
        """
        if self.device:
            q = self.device
            for i in range(q.n_chs):
                q.i[i] = 0
                print("Resetting current for channel {0} to 0 mA".format(i))
            self.device.close()
            print("Qontrol device disconnected.")
        else:
            print("No Qontrol device to disconnect.")

    # def set_current(self, channel, current):
    #     """
    #     Set the current (in mA) for a specific channel.
    #     """
    #     try:
    #         self.device.i[int(channel)] = current
    #         print("Set current for channel {0} to {1} mA".format(channel, current))
    #     except Exception as e:
    #         print("Error setting current for channel {0}: {1}".format(channel, e))

    def set_current(self, channel, current):
        """
        Set current (mA) for a specific channel with enhanced type checking
        """
        try:
            if not self.device:
                raise RuntimeError("Device not connected")
            
            channel_int = int(channel)
            if channel_int < 0 or channel_int >= self.device.n_chs:
                raise ValueError(f"Invalid channel {channel} (0-{self.device.n_chs-1})")

            # Use direct integer indexing
            self.device.i[channel_int] = current
            print(f"Set current for channel {channel_int} to {current} mA")

        except ValueError as ve:
            print(f"Invalid channel format {channel}: {ve}")
        except IndexError as ie:
            print(f"Channel {channel_int} out of range: {ie}")
        except Exception as e:
            print(f"Error setting channel {channel}: {str(e)}")
            if hasattr(self.device, 'log'):
                print(f"Last device errors: {self.device.log[-3:]}")

    def show_voltages(self):
        """
        Retrieve and print voltage readings from all channels.
        Uses the core library's get_all_values('V') method.
        """
        try:
            voltages = self.device.get_all_values('V')
            if voltages is None:
                print("No voltage readings available.")
            else:
                print("Voltage Readings:")
                for i, voltage in enumerate(voltages):
                    print("  Channel {0}: {1} V".format(i, voltage))
        except Exception as e:
            print("Error reading voltages:", e)

    def show_errors(self):
        """
        Print out any error log entries recorded by the device.
        The core library logs errors in the 'log' attribute.
        """
        try:
            errors = [entry for entry in self.device.log if entry['type'] == 'err']
            if not errors:
                print("No errors reported.")
            else:
                print("Error Log:")
                for err in errors:
                    print("  Time: {0}, Code: {1}, Channel: {2}, Description: {3}"
                          .format(err['timestamp'], err['id'], err['ch'], err['desc']))
        except Exception as e:
            print("Error retrieving error log:", e)

    def show_status(self):
        """
        Print a combined status report for all channels,
        including voltage and current readings.
        """
        try:
            voltages = self.device.get_all_values('V')
            currents = self.device.get_all_values('I')
            print("Channel Status:")
            for i in range(self.device.n_chs):
                v_str = "{0} V".format(voltages[i]) if voltages and i < len(voltages) else "N/A"
                i_str = "{0} mA".format(currents[i]) if currents and i < len(currents) else "N/A"
                print("  Channel {0}: Voltage = {1}, Current = {2}".format(i, v_str, i_str))
        except Exception as e:
            print("Error retrieving channel status:", e)


# For testing the QontrolDevice wrapper:
if __name__ == "__main__":
    qontrol_device = QontrolDevice()
    qontrol_device.connect()
    time.sleep(1)  # Give the device some time to settle

    # Show voltages and errors
    qontrol_device.show_voltages()
    qontrol_device.show_errors()
    
    # qontrol_device.set_current(4, 2.5)
    # Example: set current for channel 0 to 2.5 mA
    # qontrol_device.set_current(0, 2.5)
    # time.sleep(0.5)
    
    # Optionally, show the combined status report
    qontrol_device.show_status()

    qontrol_device.disconnect()
