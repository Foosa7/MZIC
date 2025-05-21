# utils/switch/switch_mapper.py

import json
from app.imports import *

def set_switch_channels(json_config, switch1_com_port, switch2_com_port):
    """
    Configures the input and output pins on the respective switches based on the JSON configuration.

    Args:
        json_config (dict): The JSON configuration containing 'input_pin' and 'output_pin'.
        switch1_com_port (str): COM port of the first switch (handles pins 0-11).
        switch2_com_port (str): COM port of the second switch (handles pins 12-23).
    """
    try:
        input_pin = json_config['input_pin']
        output_pin = json_config['output_pin']
    except KeyError as e:
        raise ValueError(f"Missing required key in JSON config: {e}")

    def get_switch_and_channel(pin):
        if not (0 <= pin < 24):
            raise ValueError(f"Pin {pin} is invalid. Must be 0-23.")
        switch_index = pin // 12  # 0 for switch1, 1 for switch2
        channel = (pin % 12) + 1  # Convert to 1-based channel
        return switch_index, channel

    try:
        input_switch_idx, input_ch = get_switch_and_channel(input_pin)
        output_switch_idx, output_ch = get_switch_and_channel(output_pin)
    except ValueError as e:
        raise RuntimeError(f"Pin configuration error: {e}")

    # Initialize switch handlers
    switches = [
        Switch(switch1_com_port),  # Handles pins 0-11 (channels 1-12)
        Switch(switch2_com_port)   # Handles pins 12-23 (channels 1-12)
    ]

    # Set input channel
    input_switch = switches[input_switch_idx]
    if not input_switch.set_channel(input_ch):
        raise RuntimeError(f"Failed to set input channel {input_ch} on switch {input_switch_idx + 1}")

    # Set output channel
    output_switch = switches[output_switch_idx]
    if not output_switch.set_channel(output_ch):
        raise RuntimeError(f"Failed to set output channel {output_ch} on switch {output_switch_idx + 1}")

    print("[INFO] Successfully configured input and output channels.")

# Example usage:
if __name__ == "__main__":
    # Load JSON configuration (example)
    config_json = """
    {
      "input_pin": 0,
      "output_pin": 6,
      "A1": { "arms": ["TL", "BR"], "theta": "2", "phi": "0" },
      "B1": { "arms": ["TL", "TR"], "theta": "1", "phi": "0" },
      "C1": { "arms": ["BL", "BR"], "theta": "1", "phi": "0" },
      "D1": { "arms": ["TL", "TR"], "theta": "1", "phi": "0" },
      "E1": { "arms": ["BL", "BR"], "theta": "1", "phi": "0" },
      "F1": { "arms": ["TL", "TR"], "theta": "1", "phi": "0" },
      "G1": { "arms": ["BL", "BR"], "theta": "1", "phi": "0" },
      "H1": { "arms": ["TL", "TR"], "theta": "1", "phi": "0" }
    }
    """
    config = json.loads(config_json)
    
    # Set COM ports for the two switches (adjust according to your setup)
    SWITCH1_COM = "COM3"
    SWITCH2_COM = "COM4"
    
    try:
        set_switch_channels(config, SWITCH1_COM, SWITCH2_COM)
    except Exception as e:
        print(f"[ERROR] Configuration failed: {str(e)}")