# app/utils/mzi_lut.py

from app.imports import *

# Label sequence matching the physical layout
LABEL_SEQUENCE_4x4 = [
    ["A1"],
    ["A2", "B1", "C1"],
    ["C2", "D1"],
]

LABEL_SEQUENCE_6x6 = [
    ["A1"],
    ["A2", "B1", "C1"],
    ["A3", "B2", "C2", "D1", "E1"],
    ["C3", "D2", "E2", "F1"],
    ["E3", "F2"],
]

LABEL_SEQUENCE_8x8 = [
    # First diagonal (A1)
    ["A1"],
    # Second diagonal (A2, B1, C1)
    ["A2", "B1", "C1"],
    # Third diagonal (A3, B2, C2, D1, E1)
    ["A3", "B2", "C2", "D1", "E1"],
    # Fourth diagonal (A4, B3, C3, D2, E2, F1, G1)
    ["A4", "B3", "C3", "D2", "E2", "F1", "G1"],
    # Fifth diagonal (C4, D3, E3, F2, G2, H1)
    ["C4", "D3", "E3", "F2", "G2", "H1"],
    # Sixth diagonal (E4, F3, G3, H2)
    ["E4", "F3", "G3", "H2"],
    # Seventh diagonal (G4, H3)
    ["G4", "H3"]
]

CUSTOM_DIAGONAL = [
    # First diagonal 
    ["E1"],
    # Second diagonal 
    ["F1", "G1"],
]

LABEL_SEQUENCE_12x12 = [
    ["A1"],
    ["A2", "B1", "C1"],
    ["A3", "B2", "C2", "D1", "E1"],
    ["A4", "B3", "C3", "D2", "E2", "F1", "G1"],
    ["A5", "B4", "C4", "D3", "E3", "F2", "G2", "H1", "I1"],
    ["A6", "B5", "C5", "D4", "E4", "F3", "G3", "H2", "I2", "J1", "K1"],
    ["C6", "D5", "E5", "F4", "G4", "H3", "I3", "J2", "K2", "L1"],
    ["E6", "F5", "G5", "H4", "I4", "J3", "K3", "L2"],
    ["G6", "H5", "I5", "J4", "K4", "L3"],
    ["I6", "J5", "K5", "L4"],
    ["K6", "L5"]
]

LABEL_CHIP_8x8 = [
# PNN package mapping
    ["A1", "C1", "E1", "G1"],
    ["B1", "D1", "F1", "H1"],
    ["A2", "C2", "E2", "G2"],
    ["B2", "D2", "F2", "H2"],
    ["A3", "C3", "E3", "G3"],
    ["B3", "D3", "F3", "H3"],
    ["A4", "C4", "E4", "G4"]
]


#Clements
def get_label_sequence(n):
    if n == 4:
        return LABEL_SEQUENCE_4x4
    elif n == 6:
        return LABEL_SEQUENCE_6x6
    elif n == 8:
        return CUSTOM_DIAGONAL
    else:
        return LABEL_SEQUENCE_12x12
        
def map_bs_list(n, bs_list):
    """Map beam splitters to physical labels based on pre-defined sequence"""
    label_sequence = get_label_sequence(n)
    
    label_idx = 0
    mapping = {}
    
    # Flatten the label sequence
    flat_labels = [label for diagonal in label_sequence for label in diagonal]
    
    for bs in bs_list:
        if label_idx >= len(flat_labels):
            break  # Prevent index errors for large N
        label = flat_labels[label_idx]
        mapping[label] = (bs.theta, bs.phi)
        label_idx += 1
    
    return mapping

def get_json_output(n, bs_list, input_pin, output_pin):
    """
    Generate JSON output with additional metadata and formatted theta/phi values.
    """
    mapping = map_bs_list(n, bs_list)
    output = {
        "input_pin": input_pin,
        "output_pin": output_pin,
        #"output_pin_1": 7,
        #"output_pin_2": 8,
        #"output_pin_3": 9,
        "phase_shifter": "theta",  # Always set to null
        "calibration_node": "null",  # Always set to null
    }
    
    static_config = {
            "A1": {
                "arms": ["TL", "TR"],
                "theta": str(1),
                "phi": str(0),
            },
            "C1": {
                "arms": ["TL", "TR"],
                "theta": str(1),
                "phi": str(0),
            },
            "G2": {
                "arms": ["TL", "TR"],
                "theta": str(1),
                "phi": str(0),
            },
            "H1": {
                "arms": ["TL", "BL"],
                "theta": str(1),
                "phi": str(0),
            }
        }
    output.update(static_config)  # Add static configuration to the JSON output
    
    for label, (theta, phi) in mapping.items():
        output[label] = {
            "arms": ['TL', 'TR', 'BL', 'BR'],
            "theta": str(theta),  # Format theta to 10 decimal places
            "phi": str(phi),     # Format phi to 10 decimal places
        }

    return output