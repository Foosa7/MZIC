# app/utils/calibrate/calibrate.py

from app.imports import *
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
        coefficients, residuals, _, _ = np.linalg.lstsq(X, voltages, rcond=None)
        a, c, d = coefficients

        resistance = a * currents**2 + c

        # Calculate additional parameters
        rmin = np.min(resistance)
        rmax = np.max(resistance)
        alpha = a / c if c != 0 else float('inf')

        return {
            'a': a,
            'c': c,
            'd': d,
            'resistances': resistance.tolist(),
            'rmin': float(rmin),
            'rmax': float(rmax),
            'alpha': float(alpha),
            'currents': currents.tolist(),
            'voltages': voltages,
            'max_current': float(end_current),
            'resistance_parameters': [float(a), float(c), float(d)]
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
        
        # Extract resistance parameters [a, c, d] from previous characterization
        if isinstance(resistance_params, dict):
            # Check if parameters are nested (newer format)
            if 'resistance_params' in resistance_params:
                params_dict = resistance_params['resistance_params']
                a, c, d = params_dict.get('a'), params_dict.get('c'), params_dict.get('d')
            else:
                # Direct format (older format)
                a, c, d = resistance_params.get('a'), resistance_params.get('c'), resistance_params.get('d')
        else:
            a, c, d = resistance_params  # assume list or tuple

        # Calculate max heating power to create uniform power spacing
        max_current = qontrol.globalcurrrentlimit
        max_resistance = a * (max_current**2) + c
        max_heating_power = max_current**2 * max_resistance
        
        # Create uniform heating power steps
        steps = 10
        heating_powers_mw = np.linspace(0, max_heating_power, steps)
        
        # Calculate corresponding currents for each power level
        currents = []
        for P in heating_powers_mw:
            if P == 0:
                currents.append(0.0)
            else:
                # Solve: P = I²(aI² + c) = aI⁴ + cI² for I
                # This becomes: aI⁴ + cI² - P = 0
                # Let x = I², then: ax² + cx - P = 0
                # Solution: x = (-c + √(c² + 4aP)) / (2a)
                discriminant = c**2 + 4*a*P
                if discriminant >= 0:
                    I_squared = (-c + np.sqrt(discriminant)) / (2*a)
                    if I_squared >= 0:
                        I = np.sqrt(I_squared)
                        currents.append(min(I, max_current))
                    else:
                        currents.append(0.0)
                else:
                    currents.append(0.0)
        
        currents = np.array(currents)
        
        # Calculate resistance values using the fitted parameters
        resistances = a * (currents**2) + c  # R(I) = a*I^2 + c

        # Measure optical powers
        optical_powers = []
        for I in currents:
            qontrol.set_current(channel, float(I))
            time.sleep(delay)
            optical_powers.append(thorlabs[0].read_power())

        # Reset current to zero
        qontrol.set_current(channel, 0.0)

        # Use heating power as x-data instead of current
        # Perform cosine fit with power data
        if io_config == "cross":
            fit_result = self.fit_cos(heating_powers_mw, optical_powers)
        else:
            fit_result = self.fit_cos_negative(heating_powers_mw, optical_powers)

        # Return results with power data
        return {
            'io_config': io_config,
            'amp': fit_result['amp'],
            'omega': fit_result['omega'],
            'phase': fit_result['phase'],
            'offset': fit_result['offset'],
            'heating_powers': heating_powers_mw.tolist(),  # Power in mW
            'optical_powers': optical_powers,
            'currents': currents.tolist(),  # Keep currents for reference
            'resistances': resistances.tolist(),  # Keep resistances for reference
            'fitfunc': fit_result['fitfunc'],
            'rawres': fit_result['rawres'],
            'resistance_parameters': [float(a), float(c), float(d)]  # Include resistance params
        }

    # def characterize_phase(self, qontrol, thorlabs, channel, io_config, resistance_params, delay=0.5):
    #     """Execute phase characterization routine using resistance data and power
        
    #     Args:
    #         qontrol: Instrument controller
    #         thorlabs: Power meter(s)
    #         channel: Channel index
    #         io_config: IO configuration string
    #         resistance_params: dict or list of [a, c, d] for this channel
    #         delay: Delay between measurements
    #     """
    #     # Get resistance parameters from previous characterization
    #     if resistance_params is None or resistance_params == 'Null':
    #         raise ValueError(f"Resistance characterization required for channel {channel} before phase characterization")
        
    #     # Extract resistance parameters [a, c, d] from previous characterization
    #     if isinstance(resistance_params, dict):
    #         a, c, d = resistance_params.get('a'), resistance_params.get('c'), resistance_params.get('d')
    #     else:
    #         a, c, d = resistance_params  # assume list or tuple

    #     # Measurement setup - same current range as resistance characterization
    #     start_current = 0
    #     end_current = qontrol.globalcurrrentlimit
    #     steps = 10
    #     currents = np.linspace(start_current, end_current, steps).astype(float)

    #     # Calculate resistance values using the fitted parameters
    #     resistances = a * (currents**2) + c  # R(I) = a*I^2 + c

    #     # Calculate heating power: P = I^2 * R(I) = I^2 * (a*I^2 + c) = a*I^4 + c*I^2
    #     heating_powers = currents**2 * resistances  # Power in watts
    #     heating_powers_mw = heating_powers  # Convert to milliwatts

    #     # Measure optical powers
    #     optical_powers = []
    #     for I in currents:
    #         qontrol.set_current(channel, float(I))
    #         time.sleep(delay)
    #         optical_powers.append(thorlabs[0].read_power())

    #     # Reset current to zero
    #     qontrol.set_current(channel, 0.0)

    #     # Use heating power as x-data instead of current
    #     # Perform cosine fit with power data
    #     if io_config == "cross":
    #         fit_result = self.fit_cos(heating_powers_mw, optical_powers)
    #     else:
    #         fit_result = self.fit_cos_negative(heating_powers_mw, optical_powers)

    #     # Return results with power data
    #     return {
    #         'io_config': io_config,
    #         'amp': fit_result['amp'],
    #         'omega': fit_result['omega'],
    #         'phase': fit_result['phase'],
    #         'offset': fit_result['offset'],
    #         'heating_powers': heating_powers_mw.tolist(),  # Power in mW
    #         'optical_powers': optical_powers,
    #         'currents': currents.tolist(),  # Keep currents for reference
    #         'resistances': resistances.tolist(),  # Keep resistances for reference
    #         'fitfunc': fit_result['fitfunc'],
    #         'rawres': fit_result['rawres'],
    #         'resistance_parameters': [float(a), float(c), float(d)]  # Include resistance params
    #     }

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
            bounds=([0, 0, -np.pi, -np.inf], [np.inf, np.inf, np.pi, np.inf])
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
            bounds=([0, 0, -np.pi, -np.inf], [np.inf, np.inf, np.pi, np.inf])
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
        from pathlib import Path
        mapping_file = Path(__file__).parent.parent / "qontrol" / "12_mode_mapping.json"
        with open(mapping_file, 'r') as f:
            label_map = json.load(f)

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
                    "a": float(params['a']),
                    "c": float(params['c']),
                    "d": float(params['d']),
                    "rmin": float(params['rmin']),
                    "rmax": float(params['rmax']),
                    "alpha": float(params['alpha'])
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
                    "frequency": float(params['omega']/(2*np.pi)),
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
        """Import calibration data from JSON format"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        resistance_params = {}
        phase_params = {}
        
        # Import resistance calibration data
        for channel, params in data['resistance_calibration'].items():
            channel_num = int(channel)
            resistance_params[channel_num] = {
                'a': params['resistance_params']['a'],
                'c': params['resistance_params']['c'],
                'd': params['resistance_params']['d'],
                'rmin': params['resistance_params']['rmin'],
                'rmax': params['resistance_params']['rmax'],
                'alpha': params['resistance_params']['alpha'],
                'currents': params['measurement_data']['currents'],
                'voltages': params['measurement_data']['voltages'],
                'max_current': params['measurement_data']['max_current'],
                'resistance_parameters': [
                    params['resistance_params']['a'],
                    params['resistance_params']['c'],
                    params['resistance_params']['d']
                ]
            }
        
        # Import phase calibration data
        for channel, params in data['phase_calibration'].items():
            channel_num = int(channel)
            
            # Recreate fit function based on io_config
            if params['phase_params']['io_config'] == 'cross':
                fit_func = self.fit_cos
            else:
                fit_func = self.fit_cos_negative
                
            phase_params[channel_num] = {
                'io_config': params['phase_params']['io_config'],
                'amp': params['phase_params']['amplitude'],
                'omega': params['phase_params']['frequency'] * 2 * np.pi,
                'phase': params['phase_params']['phase'],
                'offset': params['phase_params']['offset'],
                'currents': params['measurement_data']['currents'],
                'optical_powers': params['measurement_data']['optical_powers'],
                'fitfunc': fit_func
            }
        
        return resistance_params, phase_params