# utils/qmapper8x8.py
from app.imports import *
import json
from jsonschema import validate
from collections import defaultdict

# JSON schema for validation
MAPPING_SCHEMA = {
    "type": "object",
    "patternProperties": {
        "^[A-Z][1-9][0-9]*$": {
            "type": "object",
            "properties": {
                "theta": {"type": "integer", "minimum": 0},
                "phi": {"type": "integer", "minimum": 0}
            },
            "required": ["theta", "phi"]
        }
    },
    "additionalProperties": False
}



def export_mapping_json(label_map):
    """Exports mapping to JSON format with control_type"""
    export_data = {}
    for label, (theta, phi) in label_map.items():
        export_data[label] = {
            "theta": theta,
            "phi": phi,
            "control_type": "current"  # Add control type
        }
    return json.dumps(export_data, indent=2)

def import_mapping_json(json_str):
    """Imports and validates JSON mapping, returns label map"""
    try:
        data = json.loads(json_str)
        validate(instance=data, schema=MAPPING_SCHEMA)
        
        label_map = {}
        for label, values in data.items():
            label_map[label] = (values["theta"], values["phi"])
        return label_map
    except Exception as e:
        raise ValueError(f"Invalid mapping JSON: {str(e)}")
    
# ## Use this if A1 is at the bottom left corner
def create_label_mapping(grid_n):
    label_map = {}
    for i in range(grid_n):
        group_letter = chr(65 + i)  # 'A' to 'H'
        n_elements = 4 if i % 2 == 0 else 3
        
        # Generate labels in ascending order
        suffixes = range(1, n_elements+1) if i == grid_n-1 else range(n_elements, 0, -1)
        
        theta_start = sum(4 if k%2==0 else 3 for k in range(i))
        initial_phi = 31 + sum(3 if k%2==0 else 4 for k in range(i))
        
        for j, suffix in enumerate(suffixes):
            if i == grid_n-1:  # Special handling for last group
                theta = theta_start + (n_elements-1 - j)
                phi = (initial_phi - (n_elements-1)) + j
            else:
                theta = theta_start + j
                phi = initial_phi - j
            
            label = f"{group_letter}{suffix}"
            label_map[label] = (theta, phi)
    
    return label_map


# def create_label_mapping(grid_n):
#     label_map = []
#     for i in range(grid_n):
#         group_letter = chr(65 + i)  # 'A' to 'H' for grid_n=8
#         n_elements = 4 if i % 2 == 0 else 3
        
#         # Determine suffix order
#         if i == grid_n - 1:
#             suffixes = range(1, n_elements + 1)
#         else:
#             suffixes = range(n_elements, 0, -1)
        
#         # Calculate theta_start for this group
#         theta_start = sum(4 if k % 2 == 0 else 3 for k in range(i))
        
#         # Calculate initial_phi for this group
#         sum_delta_phi = sum(3 if k % 2 == 0 else 4 for k in range(i))
#         initial_phi = 31 + sum_delta_phi
        
#         for j, suffix in enumerate(suffixes):
#             # Determine theta
#             if i == grid_n - 1:
#                 theta = theta_start + (n_elements - 1 - j)
#             else:
#                 theta = theta_start + j
            
#             # Determine phi
#             if i == grid_n - 1:
#                 start_phi = initial_phi - (n_elements - 1)
#                 phi = start_phi + j
#             else:
#                 phi = initial_phi - j

#             label = f"{col_letter}{cross_num}"
#             phi_ch = phi_base - (cross_num - 1)  # Phi decreases
#             theta_ch = theta_base + (cross_num - 1)  # Theta increases
#             label_map[label] = (theta_ch, phi_ch)
        
            
#             # label = f"{group_letter}{suffix}"
#             # label_map.append((label, theta, phi))
    
#     return label_map

# ## Use this if A1 is at the bottom left corner
# def create_label_mapping(grid_n):
#     """
#     Creates mapping with phi starting at 31 and theta at 0
#     - Phi channels decrease from column base
#     - Theta channels increase from column base
#     - Column bases follow adjusted pattern
#     """
#     label_map = {}
    
#     # Initial bases - swapped values
#     phi_base = 31  # Now phi starts at 31
#     theta_base = 0  # Theta starts at 0
#     prev_phi = phi_base
#     prev_theta = theta_base
    
#     for col in range(grid_n):
#         col_letter = chr(ord('A') + col)
        
#         # Determine number of crosses in column
#         if col % 2 == 0:
#             num_crosses = grid_n // 2
#         else:
#             num_crosses = (grid_n // 2) - 1

#         # Update bases for new column (pattern alternates +4/+3)
#         if col > 0:
#             if col % 2 == 1:  # Odd columns get +4 phi, +3 theta
#                 phi_base = prev_phi + 4
#                 theta_base = prev_theta + 3
#             else:  # Even columns get +3 phi, +4 theta
#                 phi_base = prev_phi + 3
#                 theta_base = prev_theta + 4
#             prev_phi = phi_base
#             prev_theta = theta_base

#         # Assign channel pairs for each cross
#         for cross_num in range(1, num_crosses + 1):
#             label = f"{col_letter}{cross_num}"
#             phi_ch = phi_base - (cross_num - 1)  # Phi decreases
#             theta_ch = theta_base + (cross_num - 1)  # Theta increases
#             label_map[label] = (theta_ch, phi_ch)
    
#     return label_map


def print_mapping(label_map):
    """Prints mapping in column groups with channel pairs"""
    # Group by column
    columns = defaultdict(list)
    for label, chs in label_map.items():
        col = label[0]
        columns[col].append((label, chs))
    
    # Print sorted columns
    for col in sorted(columns.keys()):
        print(f"Column {col}:")
        # Sort numerically within column
        for label, (theta, phi) in sorted(columns[col], key=lambda x: int(x[0][1:])):
            print(f"  {label}: θ{theta}, φ{phi}")
        print()


def apply_grid_mapping(qontrol_device, grid_data, grid_size):
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

def clamp_value(value, max_limit):
    """Safely clamp input values"""
    try:
        val = float(value)
        return max(min(val, max_limit), 0.0)
    except (ValueError, TypeError):
        return 0.0

def apply_qontrol_mapping(qontrol_device, channel_map):
    """Apply mapped values to physical device"""
    if not qontrol_device.device:
        print("Qontrol device not connected")
        return
    
    for channel, current in channel_map.items():
        try:
            qontrol_device.set_current(channel, current)
        except Exception as e:
            print(f"Channel {channel} error: {str(e)}")


# Example usage:
if __name__ == "__main__":
    # Create and export
    mapping = create_label_mapping(8)
    json_data = export_mapping_json(mapping)
    print("Exported JSON:\n", json_data)
    
    # Import and validate
    imported_map = import_mapping_json(json_data)
    print("\nImported mapping:")
    print_mapping(imported_map)
