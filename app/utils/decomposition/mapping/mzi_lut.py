# app/utils/mzi_lut.py

from app.imports import *

# Interferometer package mapping
SEQUENCE_INTERFEROMETER_8x8 = [
    ["A1"],
    ["A2", "B1", "C1"],
    ["A3", "B2", "C2", "D1", "E1"],
    ["A4", "B3", "C3", "D2", "E2", "F1", "G1"],
    ["C4", "D3", "E3", "F2", "G2", "H1"],
    ["E4", "F3", "G3", "H2"],
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

# PNN package mapping
SEQUENCE_PNN_8x8 = [
    ["A1", "C1", "E1", "G1"],
    ["B1", "D1", "F1", "H1"],
    ["A2", "C2", "E2", "G2"],
    ["B2", "D2", "F2", "H2"],
    ["A3", "C3", "E3", "G3"],
    ["B3", "D3", "F3", "H3"],
    ["A4", "C4", "E4", "G4"]
]

SEQUENCE_PNN_12x12 = [
    ["A1", "C1", "E1", "G1", "I1", "K1"],
    ["B1", "D1", "F1", "H1", "J1", "L1"],
    ["A2", "C2", "E2", "G2", "I2", "K2"],
    ["B2", "D2", "F2", "H2", "J2", "L2"],
    ["A3", "C3", "E3", "G3", "I3", "K3"],
    ["B3", "D3", "F3", "H3", "J3", "L3"],
    ["A4", "C4", "E4", "G4", "I4", "K4"],
    ["B4", "D4", "F4", "H4", "J4", "L4"],
    ["A5", "C5", "E5", "G5", "I5", "K5"],
    ["B5", "D5", "F5", "H5", "J5", "L5"],
    ["A6", "C6", "E6", "G6", "I6", "K6"]
]

# -----------------------------------
# -----------------------------------

def get_sequence_interferometer(n):
    if n == 8:
        return SEQUENCE_INTERFEROMETER_8x8
    elif n == 12:
        return SEQUENCE_INTERFEROMETER_12x12
    else:
        raise ValueError("Unsupported interferometer mapping sequence for n={}".format(n))
        
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

        '''
        # Route out leakage light
        if label in ['B1', 'C2', 'D2', 'E3', 'E2', 'F3', 'G4', 'D1', 'F2', 'G3', 'H3']:
            output[label] = {
                "arms": ['TL', 'TR', 'BL', 'BR'],
                "theta": '2',
                "phi": '0',
            }
        
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

def get_sequence_pnn(n):
    if n == 8:
        return SEQUENCE_PNN_8x8  # 注意这里用的是 LABEL_CHIP_8x8
    elif n == 12:
        return SEQUENCE_PNN_12x12
    else:
        raise ValueError("Unsupported PNN mapping sequence for n={}".format(n))

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
    
        '''
        # Route out leakage light
        if label in ['B1', 'C2', 'D2', 'E3', 'E2', 'F3', 'G4', 'D1', 'F2', 'G3', 'H3']:
            output[label] = {
                "arms": ['TL', 'TR', 'BL', 'BR'],
                "theta": '2.0',
                "phi": '0',
            }
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