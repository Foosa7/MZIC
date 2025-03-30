from app.imports import *

class Switch:
    def __init__(self, port, baudrate=115200, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

    def _checksum(self, data):
        return sum(data) & 0xFF

    def _open_serial(self):
        return serial.Serial(self.port, baudrate=self.baudrate, timeout=self.timeout)

    def set_channel(self, channel):
        """
        Sets the switch to the specified channel.
        channel = 0 (block), or 1 to 64 depending on your device.
        """
        if not (0 <= channel <= 64):
            raise ValueError("Channel must be between 0 and 64")

        command = [0xEF, 0xEF, 0x04, 0xFF, 0x04, channel]
        command.append(self._checksum(command))

        with self._open_serial() as ser:
            ser.write(bytes(command))
            response = ser.read(7)

        if len(response) == 7 and response[4] == 0xEE:
            print(f"[INFO][Switch] channel {channel} set successfully.")
            return True
        else:
            print(f"[INFO][Switch] Failed to set channel. Response: {response.hex()}")
            return False

    def get_channel(self):
        """
        Queries the switch to find the currently active channel.
        Returns the channel number or None if communication fails.
        """
        command = [0xEF, 0xEF, 0x03, 0xFF, 0x02]
        command.append(self._checksum(command))

        with self._open_serial() as ser:
            ser.write(bytes(command))
            response = ser.read(7)

        if len(response) == 7 and response[3] == 0x02:
            current_channel = response[5]
            print(f"[INFO][Switch] Current active channel: {current_channel}")
            return current_channel
        else:
            print(f"[INFO][Switch] Failed to get channel. Response: {response.hex()}")
            return None
