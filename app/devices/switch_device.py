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
        if not (1 <= channel <= 64):
            raise ValueError("Channel must be between 1 and 64")

        command = [0xEF, 0xEF, 0x06, 0xFF, 0x0D, 0x00, 0x00, channel]
        command.append(self._checksum(command))

        print(f"[DEBUG] Sending command: {bytes(command).hex()}")

        with self._open_serial() as ser:
            ser.write(bytes(command))
            time.sleep(0.2)
            response = ser.read(7)

        if response:
            print(f"[DEBUG] Received response: {response.hex()}")
        else:
            print(f"[ERROR] No response received — device may be ignoring command.")

        if len(response) >= 6 and response[5] == 0xEE:
            print(f"[INFO][Switch] Channel {channel} set successfully.")
            return True
        else:
            print(f"[WARN][Switch] Failed to set channel. Response: {response.hex() if response else 'None'}")
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

        if len(response) == 7 and response[4] == 0x02:
            current_channel = response[5]
            print(f"[INFO][Switch] Current active channel: {current_channel}")
            return current_channel
        else:
            print(f"[INFO][Switch] Failed to get channel. Response: {response.hex()}")
            return None

## ef ef 06 ff 0d 00 00 01 f1 for channel 1
## ef ef 06 ff 0d 00 00 02 f2 for channel 2
## ef ef 06 ff 0d 00 00 03 f3 for channel 3