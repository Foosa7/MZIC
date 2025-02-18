# app/utils/angle_mapper.py
import json
#from clemens import clemens_decomposition
#from qoptcraft.operators import haar_random_unitary

def build_angle_json(angle_list, grid_size):
    """
    Builds a JSON string matching the data structure that grid.py expects
    when calling import_paths_json(...). Each cross label will map to
    { "arms": [], "theta": "<value>", "phi": "<value>" }.

    Args:
        grid_size (int): The same 'n' used in grid.py (e.g., 8).
        angle_list (list of tuples): [(θ1, φ1), (θ2, φ2), ...]. Each entry is
                                     assigned to one cross in the order we
                                     traverse them.

    Returns:
        str: A JSON string keyed by cross labels (e.g. "A1", "B3", etc.)
             with the specified or default (0,0) angles.

    Example Output:
        {
          "A1": {"arms": ["TL", "TR", "BL", "BR"], "theta": "10", "phi": "20"},
          "A2": {"arms": ["TL", "TR", "BL", "BR"], "theta": "0",  "phi": "0"},
          ...
        }
    """
    output_data = {}
    angle_index = 0
    
    for col in range(grid_size):
        letter = chr(ord('A') + col)
        
        # even columns -> n//2 crosses; odd -> (n//2) - 1
        if col % 2 == 0:
            row_count = grid_size // 2
        else:
            row_count = (grid_size // 2) - 1
        
        for row in range(row_count):
            cross_label = f"{letter}{row + 1}"
            theta_val, phi_val = angle_list[angle_index]
            output_data[cross_label] = {
                "arms": ["TL", "TR", "BL", "BR"],
                "theta": str(theta_val),
                "phi": str(phi_val)
            }
            
            angle_index += 1
    
    return json.dumps(output_data)

"""
modes = 8
unitary = haar_random_unitary(modes)
left, diag, right, left_angles, right_angles = clemens_decomposition(unitary)
angles = left_angles + right_angles
mapping = build_angle_json(angles, modes)
"""