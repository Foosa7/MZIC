# app/utils/calibrate/calibrate.py

from app.imports import *
from app.utils.appdata import AppData
from app.utils.qontrol.mapping_utils import get_mapping_functions
import numpy as np
from scipy import optimize
import matplotlib.pyplot as plt
from datetime import datetime
import time
import json


class CalibrationUtils:
    def characterize_resistance(self, qontrol, channel, delay=0.5):
        """Execute characterization routine with linear+cubic fit analysis"""
        # Measurement setup
        start_current = 0
        end_current = qontrol.globalcurrrentlimit
        steps = 10
        currents = np.linspace(start_current, end_current, steps).astype(float)
        voltages = []

        # Current sweep measurement
        for I in currents:
            qontrol.set_current(channel, float(I))
            time.sleep(delay)
            voltages.append(float(qontrol.device.v[channel]))
        
        # Reset current to zero
        qontrol.set_current(channel, 0.0)

        # Cubic+linear fit
        X = np.vstack([currents**3, currents, np.ones_like(currents)]).T
        coefficients, residuals, rank, s = np.linalg.lstsq(X, voltages, rcond=None)
        a_res, c_res, d_res = coefficients
        # UNITS:
        # [a_res] = V/(mA)³ = 1e9*Ω/A² = GΩ/A²
        # [c_res] = V/mA = 1e3*Ω = kΩ
        # [d_res] = V

        resistance = a_res * currents**2 + c_res
        # [resistance] = V/mA = 1e3*Ω = kΩ
        
        # Calculate additional parameters
        rmin = np.min(resistance) #kΩ
        rmax = np.max(resistance) #kΩ
        alpha_res = a_res / c_res if c_res != 0 else float('inf') #unitless
        print(a_res, c_res, d_res, rmin, rmax, alpha_res)
        return {
            'a_res': a_res, # V/(mA)³ = GΩ/A²
            'c_res': c_res, # V/mA = kΩ
            'd_res': d_res, # V
            'resistances': resistance.tolist(), # kΩ
            'rmin': float(rmin), # kΩ
            'rmax': float(rmax), # kΩ
            'alpha_res': float(alpha_res), # unitless
            'currents': currents.tolist(), # mA
            'voltages': voltages, # V
            'max_current': float(end_current), # mA
            'resistance_parameters': [float(a_res), float(c_res), float(d_res)]
        }


    def characterize_phase(self, qontrol, thorlabs, channel, io_config, resistance_params, delay=0.5):
        """Execute phase characterization routine using resistance data and power
        
        Args:
            qontrol: Instrument controller
            thorlabs: Power meter(s)
            channel: Channel index
            io_config: IO configuration string
            resistance_params: dict or list of [a, c, d] for this channel
            delay: Delay between measurements
        """
        # Get resistance parameters from previous characterization
        if resistance_params is None or resistance_params == 'Null':
            raise ValueError(f"Resistance characterization required for channel {channel} before phase characterization")
        
        # Extract resistance parameters [a_res, c_res, d_res] from previous characterization
        if isinstance(resistance_params, dict):
            # Check if parameters are nested (newer format)
            if 'resistance_params' in resistance_params:
                params_dict = resistance_params['resistance_params']
                a_res, c_res, d_res = params_dict.get('a_res'), params_dict.get('c_res'), params_dict.get('d_res')
            else:
                # Direct format (older format)
                a_res, c_res, d_res = resistance_params.get('a_res'), resistance_params.get('c_res'), resistance_params.get('d_res')
        else:
            a_res, c_res, d_res = resistance_params  # assume list or tuple

        # Calculate max heating power to create uniform power spacing
        max_current = qontrol.globalcurrrentlimit # mA
        max_resistance = a_res * (max_current**2) + c_res # kΩ
        max_heating_power = max_current**2 * max_resistance # mW
        
        # Create uniform heating power steps
        steps = 50
        heating_powers_mw = np.linspace(0, max_heating_power, steps)
        
        # Calculate corresponding currents for each power level
        currents = []
        for P_mW in heating_powers_mw:
            if P_mW == 0:
                currents.append(0.0)
            else:
                # Solve: P = I²(aI² + c) = aI⁴ + cI² for I
                # This becomes: aI⁴ + cI² - P = 0
                # Let x = I², then: ax² + cx - P = 0
                # Solution: x = (-c + √(c² + 4aP)) / (2a)
                discriminant = c_res**2 + 4*a_res*P_mW
                if discriminant >= 0:
                    I_squared = (-c_res + np.sqrt(discriminant)) / (2*a_res) # (mA)²
                    if I_squared >= 0:
                        I = np.sqrt(I_squared) # mA
                        currents.append(min(I, max_current))
                    else:
                        currents.append(0.0)
                else:
                    currents.append(0.0)
        
        currents = np.array(currents)
        
        # Calculate resistance values using the fitted parameters
        resistances = a_res * (currents**2) + c_res  # R(I) = a*I^2 + c

        # Measure optical powers
        optical_powers = []
        for I in currents:
            qontrol.set_current(channel, float(I)) # Set current in mA
            time.sleep(delay)
            optical_powers.append(thorlabs[0].read_power(unit='W') * 1000)  # Read power in W, convert to mW
            print(optical_powers[-1])
        # Reset current to zero
        qontrol.set_current(channel, 0.0)

        # Use heating power as x-data instead of current
        # Perform cosine fit with power data
        if io_config == "cross":
            fit_result = self.fit_cos(heating_powers_mw, optical_powers)
            print(f"[DEBUG] Using positive cosine fit for io_config={io_config}")
        else:
            fit_result = self.fit_cos_negative(heating_powers_mw, optical_powers)
            print(f"[DEBUG] Using negative cosine fit for io_config={io_config}")

        # Return results with power data
        return {
            'io_config': io_config,
            'amp': fit_result['amp'], # mW
            'omega': fit_result['omega'], # in rad/mW
            'phase': fit_result['phase'], # rad
            'offset': fit_result['offset'], # mW
            'heating_powers': heating_powers_mw.tolist(),  # power in mW
            'optical_powers': optical_powers,              # mW
            'currents': currents.tolist(),  # Keep currents for reference
            'resistances': resistances.tolist(),  # Keep resistances for reference
            'fitfunc': fit_result['fitfunc'],
            'rawres': fit_result['rawres'],
            'resistance_parameters': [float(a_res), float(c_res), float(d_res)]  # Include resistance params
        }


    def fit_cos(self, xdata, ydata):
        """Positive cosine fit"""
        guess_freq = 1/20
        guess_amp = np.std(ydata) * 2.**0.5
        guess_offset = np.mean(ydata)
        guess = [guess_amp, 2.*np.pi*guess_freq, 0., guess_offset]
        
        def cos_func(P, A, b, c, d):
            return A * np.cos(b*P + c) + d

        popt, pcov = optimize.curve_fit(
            cos_func, xdata, ydata, p0=guess,
            bounds=([0, 0, -2*np.pi, -np.inf], [np.inf, np.inf, 2*np.pi, np.inf])
        )

        A, b, c, d = popt
        return self._create_fit_result(A, b, c, d, cos_func, popt, pcov, guess)

    def fit_cos_negative(self, xdata, ydata):
        """Negative cosine fit"""
        guess_freq = 1/20
        guess_amp = np.std(ydata) * 2.**0.5
        guess_offset = np.mean(ydata)
        guess = [guess_amp, 2.*np.pi*guess_freq, 0., guess_offset]

        def cos_func(P, A, b, c, d):
            return -A * np.cos(b*P + c) + d

        popt, pcov = optimize.curve_fit(
            cos_func, xdata, ydata, p0=guess,
            bounds=([0, 0, -2*np.pi, -np.inf], [np.inf, np.inf, 2*np.pi, np.inf])
        )

        A, b, c, d = popt
        return self._create_fit_result(A, b, c, d, cos_func, popt, pcov, guess)

    def _create_fit_result(self, A, b, c, d, cos_func, popt, pcov, guess):
        """Package fit results consistently"""
        return {
            'amp': A,
            'omega': b,
            'phase': c,
            'offset': d,
            'freq': b/(2.*np.pi),
            'period': 1/(b/(2.*np.pi)),
            'fitfunc': cos_func,
            'maxcov': np.max(pcov),
            'rawres': (guess, popt, pcov)
        }


    def export_calibration(self, resistance_params, phase_params, filepath=None):
        """Export calibration data to JSON format"""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"calibration_data_{timestamp}.json"

        # Load label mapping from 12_mode_mapping.json
        # from pathlib import Path
        # mapping_file = Path(__file__).parent.parent / "qontrol" / "12_mode_mapping.json"
        # with open(mapping_file, 'r') as f:
        #     label_map = json.load(f)

        create_label_mapping, apply_grid_mapping = get_mapping_functions(self.grid_size)
        label_map = create_label_mapping(int(self.grid_size.split('x')[0]))


        # Prepare resistance data with label_theta keys and channel info at the top
        resistance_entries = []
        for channel, params in resistance_params.items():
            label = None
            channel_type = None
            for k, v in label_map.items():
                if "theta" in v and v["theta"] == int(channel):
                    label = k
                    channel_type = "theta"
                    break
                elif "phi" in v and v["phi"] == int(channel):
                    label = k
                    channel_type = "phi"
                    break
            key = f"{label}_{channel_type}" if label and channel_type else str(channel)
            resistance_entries.append((key, {
                "pin": int(channel),
                "resistance_params": {
                    "a_res": float(params['a_res']),  
                    "c_res": float(params['c_res']),  
                    "d_res": float(params['d_res']),
                    "rmin": float(params['rmin']),
                    "rmax": float(params['rmax']),
                    "alpha_res": float(params['alpha_res'])
                },
                "measurement_data": {
                    "currents": params['currents'],
                    "voltages": params['voltages'],
                    "max_current": float(params['max_current'])
                }
            }))

        # Sort by label (alphabetically)
        resistance_entries.sort(key=lambda x: x[0])
        resistance_data = {k: v for k, v in resistance_entries}

        # Prepare phase data (unchanged)
        phase_entries = []
        for channel, params in phase_params.items():
            label = None
            channel_type = None
            for k, v in label_map.items():
                if "theta" in v and v["theta"] == int(channel):
                    label = k
                    channel_type = "theta"
                    break
                elif "phi" in v and v["phi"] == int(channel):
                    label = k
                    channel_type = "phi"
                    break
            key = f"{label}_{channel_type}" if label and channel_type else str(channel)
            phase_entries.append((key, {
                "pin": int(channel),
                "phase_params": {
                    "io_config": params['io_config'],
                    "amplitude": float(params['amp']),
                    "omega": float(params['omega']),
                    "phase": float(params['phase']),
                    "offset": float(params['offset'])
                },
                "measurement_data": {
                    "currents": params['currents'],
                    "optical_powers": params['optical_powers']
                }
            }))

        # Sort by label (alphabetically)
        phase_entries.sort(key=lambda x: x[0])
        phase_data = {k: v for k, v in phase_entries}


        # Combine all calibration data
        # mesh_options = self.config.get("options", ["6x6", "8x8", "12x12"])
        calibration_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0",
                # "default_mesh": self.config.get("default_mesh", mesh_options[1])

            },
            "resistance_calibration": resistance_data,
            "phase_calibration": phase_data
        }

        # Save to file
        with open(filepath, 'w') as f:
            json.dump(calibration_data, f, indent=4)

        return filepath

    # def export_calibration(self, resistance_params, phase_params, filepath=None):
    #     """Export calibration data to JSON format"""
    #     if filepath is None:
    #         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    #         filepath = f"calibration_data_{timestamp}.json"
        
    #     # Prepare resistance data
    #     resistance_data = {}
    #     for channel, params in resistance_params.items():
    #         resistance_data[str(channel)] = {
    #             "resistance_params": {
    #                 "a": float(params['a']),
    #                 "c": float(params['c']),
    #                 "d": float(params['d']),
    #                 "rmin": float(params['rmin']),
    #                 "rmax": float(params['rmax']),
    #                 "alpha": float(params['alpha'])
    #             },
    #             "measurement_data": {
    #                 "currents": params['currents'],
    #                 "voltages": params['voltages'],
    #                 "max_current": float(params['max_current'])
    #             }
    #         }

    #     # Prepare phase data
    #     phase_data = {}
    #     for channel, params in phase_params.items():
    #         phase_data[str(channel)] = {
    #             "phase_params": {
    #                 "io_config": params['io_config'],
    #                 "amplitude": float(params['amp']),
    #                 "frequency": float(params['omega']/(2*np.pi)),
    #                 "phase": float(params['phase']),
    #                 "offset": float(params['offset'])
    #             },
    #             "measurement_data": {
    #                 "currents": params['currents'],
    #                 "optical_powers": params['optical_powers']
    #             }
    #         }

    #     # Combine all calibration data
    #     calibration_data = {
    #         "metadata": {
    #             "timestamp": datetime.now().isoformat(),
    #             "version": "1.0"
    #         },
    #         "resistance_calibration": resistance_data,
    #         "phase_calibration": phase_data
    #     }

    #     # Save to file
    #     with open(filepath, 'w') as f:
    #         json.dump(calibration_data, f, indent=4)
        
    #     return filepath


    def import_calibration(self, filepath):
        """
        Import calibration data from JSON format and save to AppData.
        
        Args:
            filepath: str, path to JSON calibration file
            
        Returns:
            Tuple of (resistance_params, phase_params) dictionaries
        """
        try:
            # Load JSON data
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            resistance_params = {}
            phase_params = {}
            
            # Import resistance calibration data
            if 'resistance_calibration_data' in data:
                for key, params in data['resistance_calibration_data'].items():
                    resistance_params[key] = {
                        'resistance_params': {
                            'a_res': float(params['resistance_params']['a']),
                            'c_res': float(params['resistance_params']['c']),
                            'd_res': float(params['resistance_params']['d']),
                            'rmin': float(params['resistance_params']['rmin']),
                            'rmax': float(params['resistance_params']['rmax']),
                            'alpha_res': float(params['resistance_params']['alpha'])
                        },
                        'measurement_data': {
                            'currents': params['measurement_data']['currents'],
                            'voltages': params['measurement_data']['voltages'],
                            'max_current': float(params['measurement_data']['max_current'])
                        },
                        'pin': int(params['pin'])
                    }
            
            # Import phase calibration data
            if 'phase_calibration_data' in data:
                for key, params in data['phase_calibration_data'].items():
                    # Recreate fit function based on io_config
                    if params['phase_params']['io_config'] == 'cross':
                        fit_func = self.fit_cos
                    else:
                        fit_func = self.fit_cos_negative
                        
                    phase_params[key] = {
                        'phase_params': {
                            'io_config': params['phase_params']['io_config'],
                            'amplitude': float(params['phase_params']['amplitude']),
                            'omega': float(params['phase_params']['omega']),
                            'phase': float(params['phase_params']['phase']),
                            'offset': float(params['phase_params']['offset'])
                        },
                        'measurement_data': {
                            'currents': params['measurement_data']['currents'],
                            'optical_powers': params['measurement_data']['optical_powers']
                        },
                        'pin': int(params['pin']),
                        'fitfunc': fit_func
                    }
            
            # Save to AppData
            AppData.resistance_calibration_data = resistance_params
            AppData.phase_calibration_data = phase_params
            
            print(f"Successfully imported calibration data from {filepath}")
            print(f"Loaded {len(resistance_params)} resistance and {len(phase_params)} phase calibrations")
            
            return resistance_params, phase_params
            
        except Exception as e:
            print(f"Error importing calibration data: {str(e)}")
            return None, None


    # def import_calibration(self, filepath):
    #     """Import calibration data from JSON format"""
    #     with open(filepath, 'r') as f:
    #         data = json.load(f)
        
    #     resistance_params = {}
    #     phase_params = {}
        
    #     # Import resistance calibration data
    #     for channel, params in data['resistance_calibration'].items():
    #         channel_num = int(channel)
    #         resistance_params[channel_num] = {
    #             'a': params['resistance_params']['a'],
    #             'c': params['resistance_params']['c'],
    #             'd': params['resistance_params']['d'],
    #             'rmin': params['resistance_params']['rmin'],
    #             'rmax': params['resistance_params']['rmax'],
    #             'alpha': params['resistance_params']['alpha'],
    #             'currents': params['measurement_data']['currents'],
    #             'voltages': params['measurement_data']['voltages'],
    #             'max_current': params['measurement_data']['max_current'],
    #             'resistance_parameters': [
    #                 params['resistance_params']['a'],
    #                 params['resistance_params']['c'],
    #                 params['resistance_params']['d']
    #             ]
    #         }
        
    #     # Import phase calibration data
    #     for channel, params in data['phase_calibration'].items():
    #         channel_num = int(channel)
            
    #         # Recreate fit function based on io_config
    #         if params['phase_params']['io_config'] == 'cross':
    #             fit_func = self.fit_cos
    #         else:
    #             fit_func = self.fit_cos_negative
                
    #         phase_params[channel_num] = {
    #             'io_config': params['phase_params']['io_config'],
    #             'amp': params['phase_params']['amplitude'],
    #             'omega': params['phase_params']['frequency'] * 2 * np.pi,
    #             'phase': params['phase_params']['phase'],
    #             'offset': params['phase_params']['offset'],
    #             'currents': params['measurement_data']['currents'],
    #             'optical_powers': params['measurement_data']['optical_powers'],
    #             'fitfunc': fit_func
    #         }
        
    #     return resistance_params, phase_params
    

    # def calculate_current_for_phase(data, channel_key, target_phase_pi):
    #     """
    #     Calculates the required current (mA) to achieve a target phase shift (in π units)
    #     for a given channel, using the linear phase model: Phase(P) = b*P + c.
    #     """
    #     print(f"Calculating Current for Channel: {channel_key}, Target: {target_phase_pi}π")

    #     # Load calibration data
    #     res_data = AppData.resistance_calibration_data(data, 'resistance')
    #     phase_data = AppData.phase_calibration_data(data, 'phase')
    #     if not res_data or channel_key not in res_data:
    #         print(f"-> Error: No resistance data for '{channel_key}'")
    #         return None
    #     if not phase_data or channel_key not in phase_data:
    #         print(f"-> Error: No phase data for '{channel_key}'")
    #         return None

    #     # Extract resistance parameters
    #     res_params = res_data[channel_key]['resistance_params']
    #     a_res = res_params.get('a', 0)
    #     c_res = res_params.get('c', 0)
    #     if c_res == 0:
    #         print("-> Error: R0 (c) parameter is zero.")
    #         return None

    #     # Extract phase calibration params
    #     ph_params = phase_data[channel_key].get('phase_params', {})
    #     b_param = ph_params.get('omega')  # in cycles per mW
    #     c_param = ph_params.get('phase')      # phase offset in rad
    #     io_conf = ph_params.get('io_config', 'cross_state')
    #     if b_param is None or c_param is None:
    #         print("-> Error: Missing phase parameters (frequency, phase offset).")
    #         return None

    #     # Convert frequency to b in rad/mW
    #     b = b_param * 2 * np.pi
    #     # Desired phase shift in rad
    #     target_phi = target_phase_pi * np.pi

    #     # Linear inversion: P (mW) = |target_phi - c_param| / b
    #     # If bar_state, phi(P) = π - (b*P + c_param) --> adjust target_phi
    #     if io_conf == 'cross_state':
    #         # invert around π
    #         target_phi_lin = np.pi - target_phi
    #         print(f"-> Bar state adjustment: target_lin = {target_phi_lin:.4f} rad")
    #     else:
    #         target_phi_lin = target_phi

    #     P_mw = abs((target_phi_lin - c_param) / b)
    #     print(f"-> Required Power: {P_mw:.4f} mW (io_config={io_conf})")

    #     # Convert to Watts
    #     P_w = P_mw / 1000.0

    #     # Resistance model: P = I^2*R0 + (a_res/c_res)*I^4*R0
    #     R0 = c_res * 1000.0
    #     alpha = a_res / c_res

    #     # Compute current
    #     if alpha == 0:
    #         I_A = np.sqrt(P_w / R0)
    #     else:
    #         I = sp.symbols('I')
    #         eq = sp.Eq(alpha * I**4 + I**2 - (P_w / R0), 0)
    #         sols = sp.solve(eq, I)
    #         real_pos = [s.evalf() for s in sols if s.is_real and s.evalf() > 0]
    #         if not real_pos:
    #             print("-> Error: No valid current solution.")
    #             return None
    #         I_A = real_pos[0]

    #     I_mA = float(I_A * 1000)
    #     print(f"-> Calculated Current: {I_mA:.4f} mA")
    #     return I_mA



# def calculate_current_for_phase(data, channel_key, target_phase_pi):
#     """
#     Compute the current (mA) to reach target phase (in units of π) using linear model.
#     """
#     res_data = get_calibration_data(data, 'resistance')
#     ph_data = get_calibration_data(data, 'phase')
#     if channel_key not in res_data or channel_key not in ph_data:
#         raise KeyError(f"Channel '{channel_key}' not found in calibration.")

#     c_res = res_data[channel_key]['resistance_params']['c']
#     R0 = c_res * 1000.0

#     ph = ph_data[channel_key]['phase_params']
#     f = ph['frequency']
#     phi0 = ph['phase']
#     io_conf = ph.get('io_config', 'cross_state')

#     target_phi = target_phase_pi * np.pi
#     if io_conf == 'cross_state':
#         target_phi_eff = np.pi - target_phi
#     else:
#         target_phi_eff = target_phi

#     b = 2 * np.pi * f
#     P_mW = abs((target_phi_eff - phi0) / b)
#     P_W = P_mW / 1000.0

#     a_res = res_data[channel_key]['resistance_params']['a']
#     alpha = a_res / c_res

#     if alpha == 0:
#         I_A = np.sqrt(P_W / R0)
#     else:
#         I = sp.symbols('I', real=True, positive=True)
#         eq = sp.Eq(alpha * I**4 + I**2 - (P_W / R0), 0)
#         sols = sp.solve(eq, I)
#         sol = [s.evalf() for s in sols if s.is_real and s > 0]
#         if not sol:
#             raise RuntimeError("No valid current solution.")
#         I_A = sol[0]

#     return float(I_A * 1000.0)