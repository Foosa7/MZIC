import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.devices.mock_devices import MockSwitch

def test_mock_switch():
    # Initialize the mock switch
    mock_switch = MockSwitch()

    # Test setting a channel
    channel_to_set = 1
    print(f"Testing set_channel with channel {channel_to_set}...")
    mock_switch.set_channel(channel_to_set)

    # Test getting the current channel
    print("Testing get_channel...")
    current_channel = mock_switch.get_channel()
    print(f"Current channel: {current_channel}")

if __name__ == "__main__":
    test_mock_switch()