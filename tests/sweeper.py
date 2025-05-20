import json

# Base dictionary
base = {
    "A1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "C1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "E1": {"arms": ["TL", "TR"], "theta": "1", "phi": "0"},
    "G1": {"arms": ["TL", "BR"], "theta": "0", "phi": "0"},
    "H1": {"arms": ["TL", "TR", "BR"], "theta": "1", "phi": "0"}
}

# Sweep G1.theta from 0 to 2
for theta in range(0, 1):
    sweep = base.copy()
    sweep["G1"] = sweep["G1"].copy()
    sweep["G1"]["theta"] = str(theta)
    print(json.dumps(sweep, separators=(',', ':')))