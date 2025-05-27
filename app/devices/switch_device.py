# app/devices/switch_device.py
from app.imports import *

class SwitchDevice:
    def __init__(self, widget, baudrate=115200, timeout=1):
        """
        widget: SwitchControlWidget instance
        """
        self.widget = widget
        self.baudrate = baudrate
        self.timeout = timeout
        self.input_port = None
        self.output_port = None
        self.connected = False

    def connect(self):
        """
        Reads the selected ports from the widget and stores them.
        """
        self.input_port, self.output_port = self.widget.get_selected_ports()
        if self.input_port:
            print(f"[INFO][Switch] Input port set to {self.input_port}")
            self.connected = True
        else:
            print("[ERROR][Switch] No input port selected!")
            self.connected = False

        if self.output_port and self.output_port != self.input_port:
            print(f"[INFO][Switch] Output port set to {self.output_port}")
        elif self.output_port:
            print(f"[INFO][Switch] Output port is same as input port: {self.output_port}")

    def _checksum(self, data):
        return sum(data) & 0xFF

    def _open_serial(self, port):
        return serial.Serial(port, baudrate=self.baudrate, timeout=self.timeout)

    def set_channel(self, channel, port_type="input"):
        """
        Set the channel on the selected switch.
        port_type: "input" or "output"
        """
        port = self.input_port if port_type == "input" else self.output_port
        if not port:
            print(f"[ERROR][Switch] {port_type.capitalize()} port not set.")
            return False

        if not (0 <= channel <= 12):
            raise ValueError("Channel must be between 1 and 64")

        command = [0xEF, 0xEF, 0x06, 0xFF, 0x0D, 0x00, 0x00, channel]
        command.append(self._checksum(command))

        print(f"[DEBUG][SWITCH] Sending command to {port}: {bytes(command).hex()}")

        with self._open_serial(port) as ser:
            ser.write(bytes(command))
            time.sleep(0.2)
            response = ser.read(7)

        if response:
            print(f"[DEBUG][SWITCH] Received response: {response.hex()}")
        else:
            print(f"[ERROR][SWITCH] No response received — device may be ignoring command.")

        if len(response) >= 6 and response[5] == 0xEE:
            print(f"[INFO][Switch] Channel {channel} set successfully on {port_type} port.")
            return True
        else:
            print(f"[WARN][Switch] Failed to set channel. Response: {response.hex() if response else 'None'}")
            return False

    def get_channel(self, port_type="input"):
        """
        Queries the switch to find the currently active channel.
        port_type: "input" or "output"
        Returns the channel number or None if communication fails.
        """
        port = self.input_port if port_type == "input" else self.output_port
        if not port:
            print(f"[ERROR][Switch] {port_type.capitalize()} port not set.")
            return None

        command = [0xEF, 0xEF, 0x03, 0xFF, 0x02]
        command.append(self._checksum(command))

        with self._open_serial(port) as ser:
            ser.write(bytes(command))
            response = ser.read(7)

        if len(response) == 7 and response[4] == 0x02:
            current_channel = response[5]
            print(f"[INFO][Switch] Current active channel on {port_type} port: {current_channel}")
            return current_channel
        else:
            print(f"[INFO][Switch] Failed to get channel. Response: {response.hex()}")
            return None

## ef ef 06 ff 0d 00 00 01 f1 for channel 1
## ef ef 06 ff 0d 00 00 02 f2 for channel 2
## ef ef 06 ff 0d 00 00 03 f3 for channel 3