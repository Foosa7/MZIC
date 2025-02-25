# app/utils/mzi_lut.py
import json
from app.imports import *

# Label sequence matching the physical layout
LABEL_SEQUENCE = [
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

def map_bs_list(bs_list):
    """Map beam splitters to physical labels based on pre-defined sequence"""
    label_idx = 0
    mapping = {}
    
    # Flatten the label sequence
    flat_labels = [label for diagonal in LABEL_SEQUENCE for label in diagonal]
    
    for bs in bs_list:
        if label_idx >= len(flat_labels):
            break  # Prevent index errors for large N
        label = flat_labels[label_idx]
        mapping[label] = (bs.theta, bs.phi)
        label_idx += 1
    
    return mapping, flat_labels

def get_json_output(n, bs_list):
    """
    New version: Directly map BS list to physical layout
    """
    mapping, flat = map_bs_list(bs_list)
    output = {}
    
    for label, (theta, phi) in mapping.items():
        
        # Round the theta and phi values        
        theta_rounded = round(theta, 2)
        phi_rounded = round(phi, 2)
        
        output[label] = {
            "arms": ["TL", "TR", "BL", "BR"],
            "theta": str(theta_rounded),
            "phi": str(phi_rounded)
        }
    
    return json.dumps(output, indent=4, sort_keys=True)