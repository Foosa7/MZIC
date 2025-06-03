import os
import numpy as np
import json

# ----- static part of the configuration -----
base = {
    "A1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "C1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "E1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "G1": {"arms": ["TL", "TR"], "theta": "2", "phi": "0"},
}

# ----- build and export newline-delimited JSON with string values -----
relative_path = r"tests\interpolation\json_steps"
os.makedirs(relative_path, exist_ok=True)  # Ensure the directory exists

output_filename = "H1_theta.json"
output_path = os.path.join(relative_path, output_filename)

with open(output_path, "w") as f:
    for t in np.linspace(0, 2, 200):
        frame = {
            **base,
            "H1": {
                "arms": ["TL", "BR"],
                "theta": str(round(float(t), 2)),
                "phi": 0,
            },
        }
        # Dump compact JSON (no spaces) and write one object per line
        f.write(json.dumps(frame, separators=(',', ':')) + "\n")

print(f"Exported frames to {output_path}")


'''
STATIC BASE CONFIGURATION: E1_theta
    "A1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "C1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "G1": {"arms": ["TL", "TR"], "theta": "2", "phi": "0"},
    "F1": {"arms": ["TL", "TR"], "theta": "2", "phi": "0"},
    "H1": {"arms": ["TL", "TR"], "theta": "2", "phi": "0"},
    "G2": {"arms": ["TL", "TR"], "theta": "2", "phi": "0"},
    "H2": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},


STATIC BASE CONFIGURATION: E2_theta
    "A1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "C1": {"arms": ["TL", "TR"], "theta": "2", "phi": "0"},
    "G1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "D1": {"arms": ["TL", "TR"], "theta": "2", "phi": "0"},
    "F1": {"arms": ["TL", "TR"], "theta": "2", "phi": "0"},
    "H1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "G2": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "F2": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "H2": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},


STATIC BASE CONFIGURATION: F1_theta
    "A1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "C1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "E1": {"arms": ["TL", "TR"], "theta": "2", "phi": "0"},
    "G1": {"arms": ["TL", "TR"], "theta": "2", "phi": "0"},
    "H1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "G2": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},


STATIC BASE CONFIGURATION: G1_theta
    "A1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "C1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "E1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "H1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},


STATIC BASE CONFIGURATION: G2_theta
    "A1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "C1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "E1": {"arms": ["TL", "TR"], "theta": "2", "phi": "0"},
    "F1": {"arms": ["TL", "TR"], "theta": "2", "phi": "0"},
    "H1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "H2": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},


STATIC BASE CONFIGURATION: H1_theta
    "A1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "C1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "E1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "G1": {"arms": ["TL", "TR"], "theta": "2", "phi": "0"},

'''