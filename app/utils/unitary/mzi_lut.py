# app/utils/mzi_lut.py
import json
import math
from app.imports import *
#import numpy as np
#from pnn.methods import decompose_clements, reconstruct_clements
from app.utils.unitary import mzi_shift

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
'''
def get_label_sequence(n):
    if n == 4:
        return LABEL_SEQUENCE_4x4
    elif n == 6:
        return LABEL_SEQUENCE_6x6
    elif n == 8:
        return LABEL_SEQUENCE_8x8
    else:
        return LABEL_SEQUENCE_12x12
'''

def get_label_sequence(n):
    if n == 4:
        return LABEL_SEQUENCE_4x4
    elif n == 6:
        return LABEL_SEQUENCE_6x6
    elif n == 8:
        return LABEL_CHIP_8x8
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



def map_pnn(n, A_theta, A_phi):
    """Map beam splitters to physical labels based on pre-defined sequence"""
    label_sequence = get_label_sequence(n)

    A_theta = A_theta.flatten()
    A_phi = A_phi.flatten()

    N_length = len(A_theta)
    
    label_idx = 0
    mapping = {}
    
    # Flatten the label sequence
    flat_labels = [label for diagonal in label_sequence for label in diagonal]

    for i in range(N_length):
        if label_idx >= len(flat_labels):
            break  # Prevent index errors for large N
        
        '''
        if i in [7, 11, 2, 10]:
            A_phi[i] += 1.0
            A_phi[i] = A_phi[i] % 2
        '''
        label = flat_labels[label_idx]
        mapping[label] = (A_theta[i], A_phi[i])
        label_idx += 1
    
    return mapping


'''
def get_json_output(n, bs_list):
    """
    New version: Directly map BS list to physical layout
    """
    mapping = map_bs_list(n, bs_list)
    output = {}
    
    for label, (theta, phi) in mapping.items():
        
        output[label] = {
            "arms": ['TL', 'TR', 'BL', 'BR'],	
            "theta": str(theta),
            "phi": str(phi),
        }
        
    return output
'''


def get_json_output(n, A_theta, A_phi):
    """
    New version: Directly map BS list to physical layout
    """
    mapping = map_pnn(n, A_theta, A_phi)
    output = {}
    
    for label, (theta, phi) in mapping.items():
        
        if label in ["E1", "E2", "H1", "G2"]:
            phi = phi + 1.0
        """
        if label in ["E1", "E2", "F1", "G1", "G2", "H1"]:
            theta = theta + mzi_shift.ps_pi(label, theta)
            
        theta = theta % 2
        """
        phi = phi % 2
        
    
        output[label] = {
            "arms": ['TL', 'TR', 'BL', 'BR'],	
            "theta": str(theta),
            "phi": str(phi),
        }
        
    return output


'''
def main():
    
    U = np.eye(8)
    
    [A_phi, A_theta, alpha] = decompose_clements(U, block='mzi')
    A_theta *= 2/np.pi
    A_phi += np.pi
    A_phi = A_phi % (2*np.pi)
    A_phi /= np.pi
    output = get_json_output(8, A_theta, A_phi)
    print(output)
        
if __name__ == "__main__":
    main()
'''