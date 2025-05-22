# utils/switch/switch_mapper.py
from app.imports import *
import json
from jsonschema import validate
from collections import defaultdict
from app.utils.appdata import AppData
from app.devices.switch_device import SwitchDevice

MAPPING_SCHEMA = {
    "type": "object",
    "properties": {
        "input_pin": {"type": "integer", "minimum": 0},
        "output_pin": {"type": "integer", "minimum": 0}
    },
    "patternProperties": {
        "^[A-Z][1-9]$": {
            "type": "object",
            "properties": {
                "arms": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["TL", "TR", "BL", "BR"]
                    },
                    "minItems": 2,
                    "maxItems": 2
                },
                "theta": {"type": "string", "pattern": "^\\d+$"},
                "phi": {"type": "string", "pattern": "^\\d+$"}
            },
            "required": ["arms", "theta", "phi"],
            "additionalProperties": False
        }
    },
    "additionalProperties": False
}


def get_switch_devices_from_appdata():
    """
    Create SwitchDevice instances for input and output ports from AppData.
    Returns (input_switch, output_switch) or (None, None) if not set.
    """
    input_port = AppData.switch_port.get("input_port")
    output_port = AppData.switch_port.get("output_port")
    input_switch = SwitchDevice(input_port) if input_port else None
    output_switch = SwitchDevice(output_port) if output_port else None
    return input_switch, output_switch


def update_switch_from_json(json_data):
    """
    Update the input and output switch devices using the default JSON API.
    Sets the channel and verifies by reading back the channel.
    Returns True if both switches are set and verified, else False.
    """
    try:
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data

        # Only extract pins, skip schema validation
        input_pin = data.get("input_pin")
        output_pin = data.get("output_pin")
        if input_pin is None or output_pin is None:
            print("[ERROR][Switch] JSON missing 'input_pin' or 'output_pin'.")
            return False

        input_switch, output_switch = get_switch_devices_from_appdata()
        success = True

        if input_switch:
            print(f"[INFO][Switch] Setting input switch to channel {input_pin}...")
            if input_switch.set_channel(input_pin):
                actual = input_switch.get_channel()
                if actual != input_pin:
                    print(f"[WARN][Switch] Input switch verification failed (expected {input_pin}, got {actual})")
                    success = False
                else:
                    print(f"[INFO][Switch] Input switch set and verified.")
            else:
                print("[ERROR][Switch] Failed to set input switch channel.")
                success = False
        else:
            print("[ERROR][Switch] Input switch device not available.")
            success = False

        if output_switch:
            print(f"[INFO][Switch] Setting output switch to channel {output_pin}...")
            if output_switch.set_channel(output_pin):
                actual = output_switch.get_channel()
                if actual != output_pin:
                    print(f"[WARN][Switch] Output switch verification failed (expected {output_pin}, got {actual})")
                    success = False
                else:
                    print(f"[INFO][Switch] Output switch set and verified.")
            else:
                print("[ERROR][Switch] Failed to set output switch channel.")
                success = False
        else:
            print("[ERROR][Switch] Output switch device not available.")
            success = False

        return success

    except Exception as e:
        print(f"[ERROR][Switch] Exception updating switch: {str(e)}")
        return False
