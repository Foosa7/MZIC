# app/utils/mzi_lut.py
import json
import math
from app.imports import *
#import numpy as np
#from pnn.methods import decompose_clements, reconstruct_clements

from tests.interpolation.data import Reader_interpolation



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


pnn_choose = 1 ## set 1 for interpolation, 0 for no interpolation
def map_pnn(n, A_theta, A_phi):
    from tests.interpolation.data import Reader_interpolation as reader
    """Map beam splitters to physical labels based on pre-defined sequence"""
    values=[
                "H1_theta_200_steps.csv",
                "G1_theta_200_steps.csv",
                "G2_theta_200_steps.csv",
                "F1_theta_200_steps.csv",
                "E1_theta_200_steps.csv",
                "E2_theta_200_steps.csv"
            ]
    label_sequence = get_label_sequence(n)

    A_theta = A_theta.flatten()
    A_phi = A_phi.flatten()
    theta_list = np.linspace(0, 2*np.pi, 200)

    N_length = len(A_theta)
    
    label_idx = 0
    mapping = {}
    
    # Flatten the label sequence
    flat_labels = [label for diagonal in label_sequence for label in diagonal]

    for i in range(N_length):
        if label_idx >= len(flat_labels):
            break  # Prevent index errors for large N
     
        
        # if i in [2, 10]:
        #     A_phi[i] = 1.5
        #     #A_phi[i] = 0.5
        # # if i in [8,9,10]:
        # #     A_theta[i] = 2.0
        # if i >= 15:
        #     A_theta[i] = 2.0
        # if i == 6:
        #     A_phi[i] = (1.5 + A_phi[3])%2
        
        if pnn_choose == 1:
            if i == 2: ## E1
                print("E1 old:", A_theta[i])
                va = values[4]
                reader.load_sweep_file(va)
                A_theta[i] = reader.theta_trans(A_theta[i]*np.pi, reader.theta, reader.theta_corrected)/ np.pi
                print("E1 new:", A_theta[i])
            if i == 3: ## G1
                print("G1 old:", A_theta[i])
                va = values[1]
                reader.load_sweep_file(va)
                A_theta[i] = reader.theta_trans(A_theta[i]*np.pi, theta_list, reader.theta_corrected)/np.pi
                print("G1 new:", A_theta[i])
            if i == 6: ## F1
                print("F1 old:", A_theta[i])
                va = values[3]
                reader.load_sweep_file(va)
                A_theta[i] = reader.theta_trans(A_theta[i]*np.pi, theta_list, reader.theta_corrected)/np.pi
                print("F1 new:", A_theta[i])
            if i == 7: ## H1
                print("H1 old:", A_theta[i])
                va = values[0]
                reader.load_sweep_file(va)
                A_theta[i] = reader.theta_trans(A_theta[i]*np.pi, theta_list, reader.theta_corrected)/np.pi
                print("H1 new:", A_theta[i])
            if i == 10: ## E2
                print("E2 old:", A_theta[i])
                va = values[5]
                reader.load_sweep_file(va)
                A_theta[i] = reader.theta_trans(A_theta[i]*np.pi, theta_list, reader.theta_corrected)/np.pi
                print("E2 new:", A_theta[i])
            if i == 11: ## G2
                print("G2 old:", A_theta[i])
                va = values[2]
                reader.load_sweep_file(va)
                A_theta[i] = reader.theta_trans(A_theta[i]*np.pi, theta_list, reader.theta_corrected)/np.pi
                print("G2 new:", A_theta[i])



        # if i in [7, 11, 2, 10]:
        #     A_phi[i] += 1
        #     A_phi[i] = A_phi[i] % 2
        
        ### The inverse measurement. In this method we measure twice for every single set of parameters
        #if i in [6, 7]:
            #A_theta[i] = 2 - A_theta[i]
        ### Correction of the theta   ### F1 and H1 shall be more important
        # if i == 3:   ####G1
        #     A_theta[i] += 0.07
        # if i == 7:   ####H1
        #     A_theta[i] += -0.12
        #     #A_theta[i] = A_theta[i] + -0.02
        #     #A_theta[i] = A_theta[i] % 2
        # if i == 11:  ####G2
        #     A_theta[i] += 0.0
        #     A_theta[i] = A_theta[i] % 2
        # 
        # if i == 6:  ### F1
        #     if A_theta[i] < 0.1:
        #         A_theta[i] += -0.025
        #     if 0.1<=A_theta[i] <=0.3:
        #         A_theta[i] += -0.02
        #     if 0.6>=A_theta[i] > 0.3:
        #         A_theta[i] +=-0.05
        #     if 0.7>=A_theta[i] > 0.6:
        #         A_theta[i] +=-0.045
        #     if 0.8>=A_theta[i] > 0.7:
        #         A_theta[i] +=-0.045
        #     if 0.85>=A_theta[i] > 0.8:
        #         A_theta[i] +=-0.045
        #     if A_theta[i] > 0.85:
        #         A_theta[i] +=-0.045
        if i == 6:
            A_theta[i] += -0.1
            
        
        # if i == 2:  ####E1
        #     A_theta[i] += -0.02
        #     A_theta[i] = A_theta[i] % 2
        
        # if i == 10:  ####E2
        #     A_theta[i] += 0.02
        #     A_theta[i] = A_theta[i] % 2
        

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

# def get_json_output(n, bs_list, input_pin, output_pin):
#     """
#     Generate JSON output with additional metadata and formatted theta/phi values.
#     """
#     mapping = map_bs_list(n, bs_list)
#     output = {}
    
#     static_config = {
#             "A1": {
#                 "arms": ["TL", "TR"],
#                 "theta": str(1),
#                 "phi": str(0),
#             },
#             "C1": {
#                 "arms": ["TL", "TR"],
#                 "theta": str(1),
#                 "phi": str(0),
#             },
#             "G2": {
#                 "arms": ["TL", "TR"],
#                 "theta": str(1),
#                 "phi": str(0),
#             },
#             "H1": {
#                 "arms": ["TL", "BL"],
#                 "theta": str(1),
#                 "phi": str(0),
#             }
#         }
#     output.update(static_config)  # Add static configuration to the JSON output
    
#     for label, (theta, phi) in mapping.items():
#         output[label] = {
#             "arms": ['TL', 'TR', 'BL', 'BR'],
#             "theta": str(theta),  # Format theta to 10 decimal places
#             "phi": str(phi),     # Format phi to 10 decimal places
#         }

#     return output