# app/utils/mzi_lut.py

from app.imports import *

# Label sequence matching the physical layout
SEQUENCE_INTERFEROMETER_4x4 = [
    ["A1"],
    ["A2", "B1", "C1"],
    ["C2", "D1"],
]

SEQUENCE_INTERFEROMETER_6x6 = [
    ["A1"],
    ["A2", "B1", "C1"],
    ["A3", "B2", "C2", "D1", "E1"],
    ["C3", "D2", "E2", "F1"],
    ["E3", "F2"],
]

SEQUENCE_INTERFEROMETER_8x8 = [
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

SEQUENCE_INTERFEROMETER_12x12 = [
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

SEQUENCE_PNN_8x8 = [
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
def get_sequence_interferometer(n):
    if n == 4:
        return SEQUENCE_INTERFEROMETER_4x4
    elif n == 6:
        return SEQUENCE_INTERFEROMETER_6x6
    elif n == 8:
        return SEQUENCE_INTERFEROMETER_8x8
    else:
        return SEQUENCE_INTERFEROMETER_12x12
        
def map_interferometer(n, bs_list):
    """Map beam splitters to physical labels based on pre-defined sequence"""
    label_sequence = get_sequence_interferometer(n)
    
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

def get_json_interferometer(n, bs_list):
    """
    Generate JSON output with additional metadata and formatted theta/phi values.
    """
    mapping = map_interferometer(n, bs_list)
    output = {}
        
    for label, (theta, phi) in mapping.items():
        output[label] = {
            "arms": ['TL', 'TR', 'BL', 'BR'],
            "theta": str(theta),  
            "phi": str(phi),     
        }

        # Route out leakage light
        if label in ['B1', 'C2', 'D2', 'E3', 'E2', 'F3', 'G4', 'D1', 'F2', 'G3', 'H3']:
            output[label] = {
                "arms": ['TL', 'TR', 'BL', 'BR'],
                "theta": '2',
                "phi": '0',
            }
        '''
        elif label == 'E1':
            output[label] = {
                "arms": ['TL', 'TR', 'BL', 'BR'],
                "theta": str(theta),
                "phi": '1.5',
            }

        elif label == 'E2':
            output[label] = {
                "arms": ['TL', 'TR', 'BL', 'BR'],
                "theta": '2.0',
                "phi": '1.5',
            }
        
        elif label == 'F1':
            output[label] = {
                "arms": ['TL', 'TR', 'BL', 'BR'],
                "theta": str(theta),
                "phi": '0.5',
            }
        
        elif label in ('G1', 'G2', 'H1'):
            output[label] = {
                "arms": ['TL', 'TR', 'BL', 'BR'],
                "theta": str(theta),
                "phi": '1.0',
            }  
        '''
    return output

# #### # Directly use A_theta and A_phi to generate JSON output for the pnn package ####
# def get_json_output_from_theta_phi(n, A_theta, A_phi):
#     """
#     直接用 A_theta 和 A_phi 生成 JSON 输出。
#     """
#     # 这里假设 A_theta 和 A_phi 是一维或二维数组，长度与 label 数量一致
#     label_sequence = get_label_sequence(n)
#     flat_labels = [label for diagonal in label_sequence for label in diagonal]
#     output = {}

#     static_config = {
#         "A1": {"arms": ["TL", "TR"], "theta": str(1), "phi": str(0)},
#         "C1": {"arms": ["TL", "TR"], "theta": str(1), "phi": str(0)},
#         "G2": {"arms": ["TL", "TR"], "theta": str(1), "phi": str(0)},
#         "H1": {"arms": ["TL", "BL"], "theta": str(1), "phi": str(0)},
#     }
#     output.update(static_config)

#     # 展平成一维
#     theta_flat = A_theta.flatten() if hasattr(A_theta, "flatten") else A_theta
#     phi_flat = A_phi.flatten() if hasattr(A_phi, "flatten") else A_phi

#     for i, label in enumerate(flat_labels):
#         if i >= len(theta_flat) or i >= len(phi_flat):
#             break
#         output[label] = {
#             "arms": ['TL', 'TR', 'BL', 'BR'],
#             "theta": str(theta_flat[i]),
#             "phi": str(phi_flat[i]),
#         }
#     return output

# PNN package mapping
def get_sequence_pnn(n):
    if n == 8:
        return SEQUENCE_PNN_8x8  # 注意这里用的是 LABEL_CHIP_8x8
    else:
        raise ValueError("Unsupported PNN sequence for n={}".format(n))

def map_pnn(n, A_theta, A_phi):
    """Map beam splitters to physical labels based on pre-defined sequence"""
    label_sequence = get_sequence_pnn(n)

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

        if i == 2:
            A_phi[i] = 0  # 这里保留原有特殊处理

        label = flat_labels[label_idx]
        mapping[label] = (A_theta[i], A_phi[i])
        label_idx += 1
    
    return mapping

def get_json_pnn(n, A_theta, A_phi):
    """
    采用PNN物理映射方式，直接用A_theta和A_phi生成JSON输出
    """
    mapping = map_pnn(n, A_theta, A_phi)
    output = {}
    for label, (theta, phi) in mapping.items():
        output[label] = {
            "arms": ['TL', 'TR', 'BL', 'BR'],
            "theta": str(theta),
            "phi": str(phi),
        }
    
        # Route out leakage light
        if label in ['B1', 'C2', 'D2', 'E3', 'E2', 'F3', 'G4', 'D1', 'F2', 'G3', 'H3']:
            output[label] = {
                "arms": ['TL', 'TR', 'BL', 'BR'],
                "theta": '2.0',
                "phi": '0',
            }
        '''
        elif label == 'E1':
            output[label] = {
                "arms": ['TL', 'TR', 'BL', 'BR'],
                "theta": str(theta),
                "phi": '1.5',
            }
        
        elif label == 'E2':
            output[label] = {
                "arms": ['TL', 'TR', 'BL', 'BR'],
                "theta": '2.0',
                "phi": '1.5',
            }
        
        elif label == 'F1':
            output[label] = {
                "arms": ['TL', 'TR', 'BL', 'BR'],
                "theta": str(theta),
                "phi": '0.5',
            }
        
        elif label in ('G1', 'G2', 'H1'):
            output[label] = {
                "arms": ['TL', 'TR', 'BL', 'BR'],
                "theta": str(theta),
                "phi": '1.0',
            }  
        '''
    return output