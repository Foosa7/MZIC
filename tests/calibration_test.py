import json
import copy
import numpy as np
import sympy as sp
import sys

class AppData:
    """Stores calibration settings loaded from the JSON file."""
    phase_calibration_data = {}
    resistance_calibration_data = {}

def get_mapping_functions(grid_size):
    """Returns the required mapping functions."""
    # This mock function is simplified as its output is no longer displayed.
    def create_label_mapping(size):
        labels = [f"{chr(ord('A') + r)}{c + 1}" for r in range(size) for c in range(size)]
        return {label: {} for label in labels}

    def apply_grid_mapping(qontrol, config_json, grid_size):
        # This function is kept for structural integrity but does not produce output.
        pass
        
    return create_label_mapping, apply_grid_mapping

class MockCustomGrid:
    """Mocks the UI grid element that holds the user's desired phase values."""
    def __init__(self, grid_data):
        self._grid_data = grid_data

    def export_paths_json(self):
        # In a real application, this would represent the user's input for phase shifts.
        # For this script, we'll use a fixed example.
        return json.dumps(self._grid_data)

class PhaseController:
    """A controller to manage and apply phase configurations."""
    def __init__(self, grid_data, grid_size='8x8'):
        self.grid_size = grid_size
        self.custom_grid = MockCustomGrid(grid_data)
        # The following attributes are kept for function compatibility.
        self.interpolation_enabled = False
        self.interpolated_theta = {}
        self.phase_grid_config = {}

    def _show_error(self, message):
        """Displays an error message and exits."""
        print(f"ERROR: {message}", file=sys.stderr)
        sys.exit(1)

    def _update_phase_results_display(self, applied, failed):
        """Displays the final results of the operation."""
        print("\n" + "="*28)
        print("Applied Phase Currents")
        print("="*28)
        if not applied:
            print("No channels were successfully applied.")
        else:
            for item in applied:
                print(f"- {item}")
        
        if failed:
            print("\n" + "-"*28)
            print("Failed or Uncalibrated Channels")
            print("-"*28)
            for item in failed:
                print(f"- {item}")

    def apply_phase_new_json(self):
        """
        Apply phase settings to the entire grid based on phase calibration data from AppData.
        Processes all theta and phi values in the current grid configuration.
        """
        try:
            grid_config = json.loads(self.custom_grid.export_paths_json())
            if not grid_config:
                self._show_error("No grid configuration found in the input data.")
                return

            create_label_mapping, apply_grid_mapping = get_mapping_functions(self.grid_size)
            label_map = create_label_mapping(int(self.grid_size.split('x')[0]))

            phase_grid_config = copy.deepcopy(grid_config)
            applied_channels = []
            failed_channels = []

            for cross_label, data in grid_config.items():
                if cross_label not in label_map:
                    continue

                # Process theta value
                theta_val = data.get("theta")
                if theta_val:
                    try:
                        theta_float = float(theta_val)
                        calib_key = f"{cross_label}_theta"
                        current_theta = self._calculate_current_for_phase_new_json(calib_key, theta_float)
                        
                        if current_theta is not None:
                            current_theta = round(current_theta, 5)
                            applied_channels.append(f"{cross_label}:θ = {current_theta:.5f} mA")
                        else:
                            failed_channels.append(f"{cross_label}:θ (no calibration)")
                    except Exception as e:
                        failed_channels.append(f"{cross_label}:θ ({str(e)})")

                # Process phi value
                phi_val = data.get("phi")
                if phi_val:
                    try:
                        phi_float = float(phi_val)
                        calib_key = f"{cross_label}_phi"
                        current_phi = self._calculate_current_for_phase_new_json(calib_key, phi_float)
                        
                        if current_phi is not None:
                            current_phi = round(current_phi, 5)
                            applied_channels.append(f"{cross_label}:φ = {current_phi:.5f} mA")
                        else:
                            failed_channels.append(f"{cross_label}:φ (no calibration)")
                    except Exception as e:
                        failed_channels.append(f"{cross_label}:φ ({str(e)})")

            self._update_phase_results_display(applied_channels, failed_channels)

        except Exception as e:
            self._show_error(f"Failed to apply phases: {str(e)}")

    def _calculate_current_for_phase_new_json(self, calib_key, phase_value):
        """
        Calculate current for a phase value, printing calculation steps.
        """
        phase_cal = AppData.phase_calibration_data.get(calib_key)
        res_cal = AppData.resistance_calibration_data.get(calib_key)
        
        if not phase_cal or not res_cal:
            return None # No calibration data for this channel

        print("\n" + "-"*35)
        print(f"Calculating: {calib_key}")
        print("-"*35)
        print(f"Target Phase: {phase_value}π")

        try:
            phase_params = phase_cal.get("phase_params", {})
            res_params = res_cal.get("resistance_params", {})
            if not phase_params or not res_params:
                print("-> Error: Missing 'phase_params' or 'resistance_params' in calibration data.")
                return None

            b = phase_params.get("frequency", 1.0) * 2 * np.pi
            c = phase_params.get("phase", 0.0)
            print(f"Phase Parameters (b, c): ({b:.5f}, {c:.5f})")
            
            if phase_value < c/np.pi:
                phase_value += 2
                print(f"-> Phase adjusted to: {phase_value}π")

            P = abs((phase_value * np.pi - c) / b)
            print(f"Required Power (P): {P:.5f} mW")
            
            a_res = res_params.get("a")
            c_res = res_params.get("c")
            
            if a_res is not None and c_res is not None:
                I = sp.symbols('I')
                P_watts = P / 1000.0
                R0 = c_res
                alpha = a_res / R0 if R0 != 0 else 0
                print(f"Resistance Parameters (R0, alpha): ({R0:.5f}, {alpha:.5f})")

                eq = sp.Eq(P_watts / R0, I**2 + alpha * I**4)
                print(f"Equation: {sp.pretty(eq, use_unicode=False)}")
                
                solutions = sp.solve(eq, I)
                positive_solutions = [sol.evalf() for sol in solutions if sol.is_real and sol.evalf() > 0]
                
                if positive_solutions:
                    current_A = positive_solutions[0]
                    current_mA = float(1000 * current_A)
                    print(f"Positive Real Solution (Amps): {current_A:.5f}")
                    print(f"Calculated Current (mA): {current_mA:.5f}")
                    return current_mA
                else:
                    print("-> Warning: No positive real solution found. Falling back to linear model.")
                    return float(1000 * np.sqrt(P / (R0 * 1000))) if R0 > 0 else 0.0
            else:
                print("-> Warning: Resistance parameters 'a' or 'c' not found. Using default linear model.")
                R_default = 50.0
                return float(1000 * np.sqrt(P / (R_default * 1000)))

        except Exception as e:
            print(f"-> Error during calculation for {calib_key}: {str(e)}")
            return None

if __name__ == "__main__":
    # Get JSON file path from user input
    json_path = r"C:\Users\hp-ma\Downloads\calibration\G4-3.292.json" #input("Enter the path to the calibration JSON file: ")

    try:
        with open(json_path, 'r') as f:
            config_data = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: The file was not found at '{json_path}'", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"ERROR: The file at '{json_path}' is not a valid JSON file.", file=sys.stderr)
        sys.exit(1)

    # Populate the AppData class with the calibration data
    AppData.resistance_calibration_data = config_data.get("resistance_calibration", {})
    AppData.phase_calibration_data = config_data.get("phase_calibration", {})
    
    # We add a 'phi' calibration for D4 to demonstrate handling multiple channels
    if "D4_theta" in AppData.resistance_calibration_data:
        AppData.resistance_calibration_data["D4_phi"] = AppData.resistance_calibration_data["D4_theta"]
    if "D4_theta" in AppData.phase_calibration_data:
        AppData.phase_calibration_data["D4_phi"] = AppData.phase_calibration_data["D4_theta"]

    # Define the target phase shifts for the grid
    target_grid_state = {
        "D4": {"theta": "1.2", "phi": "0.8"},
        "A1": {"theta": "1.0", "phi": "1.0"} # This channel has no calibration data
    }
    
    # Create an instance of our controller and run the process
    controller = PhaseController(grid_data=target_grid_state)
    controller.apply_phase_new_json()