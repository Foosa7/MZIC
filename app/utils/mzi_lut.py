# app/utils/mzi_lut.py
import json

def label_odd(i, j):
    """
    Given an odd diagonal i (i = 1,3,5,…) and an index j (0 ≤ j < i),
    return the physical label (e.g. "A1", "A2", "B1", "C1", "A3", "B2", "C2", "D1", "E2") 
    according to the desired ordering.
    
    For N = 8, for example:
      - i = 1, j = 0  → "A1"
      - i = 3, then j = 0 → "A2", j = 1 → "B1", j = 2 → "C1"
      - i = 5, then j = 0 → "A3", j = 1 → "B2", j = 2 → "C2", j = 3 → "D1", j = 4 → "E2"
    """
    # Mapping for N = 8
    if i == 1:
        return "A1"
    elif i == 3:
        mapping = {0: "A2", 1: "B1", 2: "C1"}
        return mapping[j]
    elif i == 5:
        mapping = {0: "A3", 1: "B2", 2: "C2", 3: "D1", 4: "E1"}
        return mapping[j]
    elif i == 7:
        mapping = {0: "A4", 1: "B3", 2: "C3", 3: "D2", 4: "E2", 5: "F1", 6: "G1"}
        return mapping[j]
    else:
        # Placeholder (extend later)
        return f"X{i}{j}"  

def label_even(i, j):
    """
    Given an even diagonal i (i = 2,4,6,…) and an index j (1 ≤ j ≤ i),
    return the physical label (e.g. "H3", "G4", "H2", "G3", "F3", "E4", "H1", "G2", "F2", "E3", "D2", "C3")
    according to the desired ordering.
    
    E.g. for N = 8:
      - i = 2, j = 1 → "H3", j = 2 → "G4"
      - i = 4, then j = 1 → "H2", j = 2 → "G3", j = 3 → "F3", j = 4 → "E4"
      - i = 6, then j = 1 → "H1", j = 2 → "G2", j = 3 → "F2", j = 4 → "E3", j = 5 → "D2", j = 6 → "C3"
    """
    if i == 2:
        mapping = {1: "H3", 2: "G4"}
        return mapping[j]
    elif i == 4:
        mapping = {1: "H2", 2: "G3", 3: "F3", 4: "E4"}
        return mapping[j]
    elif i == 6:
        mapping = {1: "H1", 2: "G2", 3: "F2", 4: "E3", 5: "D3", 6: "C4"}
        return mapping[j]
    else:
        return f"Y{i}{j}"  # Placeholder (extend later)

def map_angles_general(N, left_angles, right_angles):
    """
    General mapping for an N-mode interferometer.
    Uses the same loop order as in clemens.py:
      For i = 1,...,N-1:
         if i odd: loop j = 0,...,i-1, assign from right_angles (after reversing that list)
         if i even: loop j = 1,...,i, assign from left_angles.
    The physical label for each operation is obtained from label_odd or label_even.
    
    Returns:
        dict: { label: (θ, φ) } in the order defined by the decomposition.
    """
    mapping = {}
    # Copy angle lists so we don't alter originals.
    r_list = right_angles[:] 
    l_list = left_angles[:]
    # Reverse the right_angles so the first operation gets the last element.
    r_list.reverse()
    
    # Loop over diagonals.
    for i in range(1, N):
        if i % 2 == 1:
            # Odd diagonal → use r_list (T⁻¹)
            for j in range(i):
                if r_list:
                    label = label_odd(i, j)
                    mapping[label] = r_list.pop(0)
        else:
            # Even diagonal → use l_list (T)
            for j in range(1, i+1):
                if l_list:
                    label = label_even(i, j)
                    mapping[label] = l_list.pop(0)
    return mapping

def get_json_output(N, left_angles, right_angles):
    """
    Returns a JSON string representing the mapping from MZI labels to their angles.
    The output format is:
      "A1": {"arms": ["TL", "TR", "BL", "BR"], "theta": "<theta>", "phi": "<phi>"}, ...
    """
    mapping = map_angles_general(N, left_angles, right_angles)
    output = {}
    for label, (theta, phi) in mapping.items():
        output[label] = {
            "arms": ["TL", "TR", "BL", "BR"],
            "theta": str(theta),
            "phi": str(phi)
        }
    return json.dumps(output, indent=4, sort_keys=True)