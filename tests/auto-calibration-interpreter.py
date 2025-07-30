import json
from collections import defaultdict

def convert_calibration_to_grid_inline(calibration_json, get_cross_modes_func):
    """
    Convert calibration JSON to inline JSON strings per step.
    Each step is output as a single-line JSON of nodes.
    """
    lines = []
    cross_modes = get_cross_modes_func()

    for step_data in calibration_json.get("calibration_steps", []):
        grid = {}

        # Calibration node
        cal_node = step_data["calibration_node"]
        mode = step_data.get("Io_config", cross_modes.get(cal_node, "cross"))
        grid[cal_node] = {"arms": mode_to_arms(mode), "theta": "0", "phi": "0"}

        # Additional nodes
        for node, io_state in step_data.get("additional_nodes", {}).items():
            grid[node] = {"arms": mode_to_arms(io_state.lower()), "theta": "0", "phi": "0"}

        # Dump as single-line JSON
        line = json.dumps(grid, separators=(',', ':'))
        lines.append(line)

    return lines

def mode_to_arms(mode):
    """
    Convert IO mode to arms list.
    """
    if mode.lower() == "cross":
        return ["TL", "BR"]
    elif mode.lower() == "bar":
        return ["TL", "TR"]
    elif mode.lower() == "split":
        return ["TR", "BR", "TL"]
    elif mode.lower() == "arbitrary":
        return ["TL", "TR", "BL", "BR"]
    else:
        return []  # Default: no arms

# Example usage data:
calibration_json = {}
# Dummy get_cross_modes function for testing:
def dummy_get_cross_modes():
    return {"A1": "cross", "B1": "bar", "C1": "cross", "D1": "split"}

# --- Main execution ---
# Generate the grid dictionary
lines = convert_calibration_to_grid_inline(calibration_json, dummy_get_cross_modes)

with open("grid_output.jsonl", "w") as f:
    for line in lines:
        f.write(line + "\n")


print("Successfully saved output to grid_output.jsonl")