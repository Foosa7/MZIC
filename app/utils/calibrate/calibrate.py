# app/utils/calibrate/calibrate.py

import numpy as np
from scipy import optimize
import matplotlib.pyplot as plt
from datetime import datetime
import time
import json
from app.utils.qontrol.qmapper8x8 import create_label_mapping

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

    def characterize_phase(self, qontrol, thorlabs, channel, io_config, delay=0.5):
        """Execute phase characterization routine"""
        start_current = 0
        end_current = qontrol.globalcurrrentlimit
        steps = 10
        currents = np.linspace(start_current, end_current, steps)
        optical_powers = []
        
        for I in currents:
            qontrol.set_current(channel, float(I))
            time.sleep(delay)
            optical_powers.append(thorlabs[0].read_power())
        
        qontrol.set_current(channel, 0.0)

        # Perform cosine fit
        if io_config == "cross":
            fit_result = self.fit_cos(currents, optical_powers)
        else:
            fit_result = self.fit_cos_negative(currents, optical_powers)

        # Add fit_result items to the return dictionary
        return {
            'io_config': io_config,
            'amp': fit_result['amp'],
            'omega': fit_result['omega'],
            'phase': fit_result['phase'],
            'offset': fit_result['offset'],
            'currents': currents.tolist(),
            'optical_powers': optical_powers,
            'fitfunc': fit_result['fitfunc'],  
            'rawres': fit_result['rawres']     
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
        """Export calibration data to JSON format with channel labels (underscored), thetas first then phis, and pin info"""
        import json
        import numpy as np
        from datetime import datetime

        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"calibration_data_{timestamp}.json"

        label_map = create_label_mapping(8)  # Use your grid size here
        channel_to_label = {}
        for label, (theta_ch, phi_ch) in label_map.items():
            channel_to_label[theta_ch] = f"{label}_theta"
            channel_to_label[phi_ch] = f"{label}_phi"

        # Prepare resistance data
        theta_res = {}
        phi_res = {}
        for channel, params in resistance_params.items():
            label = channel_to_label.get(channel, str(channel))
            entry = {
                "pin": channel,
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
            }
            if "theta" in label:
                theta_res[label] = entry
            else:
                phi_res[label] = entry

        resistance_data = {**theta_res, **phi_res}

        # Prepare phase data
        theta_phase = {}
        phi_phase = {}
        for channel, params in phase_params.items():
            label = channel_to_label.get(channel, str(channel))
            entry = {
                "pin": channel,
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
            }
            if "theta" in label:
                theta_phase[label] = entry
            else:
                phi_phase[label] = entry

        phase_data = {**theta_phase, **phi_phase}

        calibration_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0"
            },
            "resistance_calibration": resistance_data,
            "phase_calibration": phase_data
        }

        with open(filepath, 'w') as f:
            json.dump(calibration_data, f, indent=4)

        return filepath

    def import_calibration(self, filepath):
        """Import calibration data from JSON format"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        resistance_params = {}
        phase_params = {}
        
        # Import resistance calibration data
        for label, params in data['resistance_calibration'].items():
            resistance_params[label] = {
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
        for label, params in data['phase_calibration'].items():
            # Recreate fit function based on io_config
            if params['phase_params']['io_config'] == 'cross':
                fit_func = self.fit_cos
            else:
                fit_func = self.fit_cos_negative
                
            phase_params[label] = {
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