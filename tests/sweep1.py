import numpy as np
import json

# # ----- static part of the configuration (now excluding G1) -----
# base = {
#     "A1": {"arms": ["TL", "TR"],         "theta": 1, "phi": 0},
#     "C1": {"arms": ["TL", "TR"],         "theta": 1, "phi": 0},
#     "E1": {"arms": ["TL", "TR"],         "theta": 1, "phi": 0},
#     "H1": {"arms": ["TL", "TR", "BR"],   "theta": 1, "phi": 0},
# }

# # # ----- sweep G1.theta from 0→1 in 21 steps, print one JSON per line -----
# # for t in np.linspace(0, 1, 100):
# #     frame = {
# #         **base,
# #         "G1": {"arms": ["TL", "BR"], "theta": round(float(t), 2), "phi": 0},
# #     }
# #     print(json.dumps(frame))

# config_frames = []
# for t in np.linspace(0, 1, 100):
#     frame = {
#         **base,
#         "G1": {"arms": ["TL", "BR"], "theta": round(float(t), 2), "phi": 0},
#     }
#     config_frames.append(frame)

# # ----- export to JSON file -----
# output_path = r"C:\Users\hp-ma\OneDrive\Pictures\MZIC\tests\config_frames.json"
# with open(output_path, "w") as f:
#     json.dump(config_frames, f, indent=2)

# print(f"Exported {len(config_frames)} configurations to {output_path}")


import numpy as np
import json

# ----- static part of the configuration (excluding G1) -----
base = {
    "A1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "C1": {"arms": ["TL", "TR"], "theta": "2", "phi": "0"},
    "D1": {"arms": ["TL", "TR"], "theta": "2", "phi": "0"},
    "G1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "F1": {"arms": ["TL", "TR"], "theta": "2", "phi": "0"},
    "F2": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "H1": {"arms": ["TL", "TR"], "theta": "2", "phi": "0"},
    "H2": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "G2": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
}

# ----- build and export newline-delimited JSON with string values -----
output_path = r"C:\Users\The photonic chip\GitHub\MZIC\tests\json_frames\config_frames.json"
with open(output_path, "w") as f:
    for t in np.linspace(0, 2, 200):
        frame = {
            **base,
            "E2": {
                "arms": ["TL", "BR"],
                "theta": str(round(float(t), 2)),
                "phi": 0,
            },
        }
        # Dump compact JSON (no spaces) and write one object per line
        f.write(json.dumps(frame, separators=(',', ':')) + "\n")

# print(f"Exported {21} configurations (1 JSON object per line) to {output_path}")


