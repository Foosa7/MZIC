# utils/switch/switch_mapper.py
from app.imports import *
import json
from jsonschema import validate
from collections import defaultdict

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

def apply_switch_mapping(qontrol_device, grid_data, grid_size):
    """Main function to map grid values to Qontrol channels"""
    try:
        n = int(grid_size.split('x')[0])
        label_map = create_label_mapping(n)
        
        # Parse grid export data
        export_data = json.loads(grid_data)
        channel_values = {}
        
        # Get current limit from device config
        current_limit = qontrol_device.config.get("globalcurrrentlimit")
        
        # Map values to channels
        for label, data in export_data.items():
            if label in label_map:
                theta_ch, phi_ch = label_map[label]
                
                # Clamp values to safety limits
                theta = clamp_value(data.get("theta", 0), current_limit)
                phi = clamp_value(data.get("phi", 0), current_limit)
                
                channel_values[theta_ch] = theta
                channel_values[phi_ch] = phi
        
        # Apply to Qontrol device
        apply_qontrol_mapping(qontrol_device, channel_values)
        
    except Exception as e:
        print(f"Mapping error: {str(e)}")
