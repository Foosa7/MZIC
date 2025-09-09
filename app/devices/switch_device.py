from app.imports import *

class Switch:
    def __init__(self, port_in, port_out, baudrate=115200, timeout=1):
        self.port_in = port_in
        self.port_out = port_out
        self.baudrate = baudrate
        self.timeout = timeout

    def _checksum(self, data):
        return sum(data) & 0xFF

    def _open_serial(self, port):
        return serial.Serial(port, baudrate=self.baudrate, timeout=self.timeout)

    def swap_ports(self):
        """
        Swaps the input and output ports in case Windows assigned them incorrectly.
        """
        self.port_in, self.port_out = self.port_out, self.port_in
        logging.info(f"[SWITCH] Ports swapped. Now IN={self.port_in}, OUT={self.port_out}")

    def set_channel(self, channel):
        """
        Sets the switch to the specified channel.
        channel = 0 (block), or 1 to 64 depending on your device.
        """
        if not (0 <= channel <= 64):
            raise ValueError("Channel must be between 0 and 64")

        command = [0xEF, 0xEF, 0x06, 0xFF, 0x0D, 0x00, 0x00, channel]
        command.append(self._checksum(command))

        logging.info(f"[SWITCH] Sending command to {self.port_out}: {bytes(command).hex()}")

        with self._open_serial(self.port_out) as ser:
            ser.write(bytes(command))
            response = ser.read(7)

        if response:
            logging.info(f"[SWITCH] Received response: {response.hex()}")
        else:
            logging.error(f"[SWITCH] No response received — device may be ignoring command.")

    def get_channel(self):
        """
        Queries the switch to find the currently active channel.
        Returns the channel number or None if communication fails.
        """
        command = [0xEF, 0xEF, 0x03, 0xFF, 0x02]
        command.append(self._checksum(command))

        with self._open_serial(self.port_in) as ser:
            ser.write(bytes(command))
            response = ser.read(7)

        if len(response) == 7:
            if (response[0] == 0xED and response[1] == 0xFA and response[4] == 0x02) or \
               (response[0] == 0xEF and response[1] == 0xEF and response[4] == 0x02):
                current_channel = response[5]
                logging.info(f"[Switch] Current active channel: {current_channel}")
                return current_channel
        
        logging.info(f"[Switch] Failed to get channel. Response: {response.hex()}")
        return None

## ef ef 06 ff 0d 00 00 01 f1 for channel 1
## ef ef 06 ff 0d 00 00 02 f2 for channel 2
## ef ef 06 ff 0d 00 00 03 f3 for channel 3