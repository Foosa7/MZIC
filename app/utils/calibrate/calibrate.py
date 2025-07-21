# app/utils/calibrate/calibrate.py

from app.imports import *
import numpy as np
from scipy import optimize
import matplotlib.pyplot as plt
from datetime import datetime
import time
import json

# app/utils/calibrate/calibrate.py
class CalibrationUtils:
    def characterize_resistance(self, qontrol, channel, delay=0.5):
        """Execute resistance characterization by sweeping currents (mA), converting to A for fitting, and returning SI‑unit parameters."""
        max_mA = qontrol.globalcurrrentlimit
        currents_mA = np.linspace(0.0, max_mA, 10)
        voltages = []
        for I_mA in currents_mA:
            qontrol.set_current(channel, float(I_mA))
            time.sleep(delay)
            voltages.append(float(qontrol.device.v[channel]))
        qontrol.set_current(channel, 0.0)

        currents_A = currents_mA / 1000.0
        X = np.vstack([currents_A**3, currents_A, np.ones_like(currents_A)]).T
        coeffs, residuals, _, _ = np.linalg.lstsq(X, voltages, rcond=None)
        a, c, d = coeffs
        resistances_ohm = a * currents_A**2 + c
        rmin_ohm = float(resistances_ohm.min())
        rmax_ohm = float(resistances_ohm.max())
        alpha = float(a / c) if c != 0 else float('inf')
        res_ssq = float(residuals[0]) if residuals.size > 0 else None

        return {
            'a': float(a),
            'c': float(c),
            'd': float(d),
            'residuals_ssq': res_ssq,
            'currents_mA': currents_mA.tolist(),
            'currents_A': currents_A.tolist(),
            'voltages_V': voltages,
            'resistances_ohm': resistances_ohm.tolist(),
            'rmin_ohm': rmin_ohm,
            'rmax_ohm': rmax_ohm,
            'alpha': alpha,
            'max_current_mA': float(max_mA),
            'max_current_A': float(max_mA / 1000.0)
        }

    def characterize_phase(self, qontrol, thorlabs, channel, io_config, resistance_params, delay=0.5):
        """Execute phase characterization: uniform power sweep, compute currents, measure optical, and fit cosine."""
        if not resistance_params:
            raise ValueError(f"Missing resistance_params for channel {channel}")
        if isinstance(resistance_params, dict):
            a = resistance_params.get('a', resistance_params.get('resistance_parameters', {}).get('a'))
            c = resistance_params.get('c', resistance_params.get('resistance_parameters', {}).get('c'))
        else:
            a, c, _ = resistance_params

        max_mA = qontrol.globalcurrrentlimit
        max_A = max_mA / 1000.0
        max_R = a * max_A**2 + c
        max_power_mW = max_A**2 * max_R * 1000.0
        powers_mW = np.linspace(0.0, max_power_mW, 50)

        currents_A = []
        for P in powers_mW:
            if P <= 0:
                currents_A.append(0.0)
            else:
                P_W = P / 1000.0
                disc = c**2 + 4 * a * P_W
                if disc < 0:
                    currents_A.append(0.0)
                else:
                    x = (-c + np.sqrt(disc)) / (2 * a)
                    I = np.sqrt(max(x, 0))
                    currents_A.append(min(I, max_A))
        currents_A = np.array(currents_A)

        optical_powers = []
        for I in currents_A:
            qontrol.set_current(channel, I * 1000.0)
            time.sleep(delay)
            optical_powers.append(thorlabs[0].read_power())
        qontrol.set_current(channel, 0.0)

        fit_method = self.fit_cos if io_config == 'cross_state' else self.fit_cos_negative
        fit_res = fit_method(powers_mW, optical_powers)

        return {
            'io_config': io_config,
            'a': float(a),
            'c': float(c),
            'amp': fit_res['amp'],
            'omega': fit_res['omega'],
            'phase': fit_res['phase'],
            'offset': fit_res['offset'],
            'ssq': fit_res['ssq'],
            'maxcov': fit_res['maxcov'],
            'powers_mW': powers_mW.tolist(),
            'currents_A': currents_A.tolist(),
            'currents_mA': (currents_A * 1000.0).tolist(),
            'optical_powers': optical_powers
        }

    def fit_cos(self, xdata, ydata):
        """Bounded positive cosine fit with diagnostics."""
        x = np.array(xdata)
        y = np.array(ydata)
        amp0 = (y.max() - y.min()) / 2
        d0 = y.mean()
        freq0 = 1.0 / (x[-1] - x[0] + 1e-9)
        p0 = [amp0, 2*np.pi*freq0, 0.0, d0]

        def model(x, A, b, phi, d): return A * np.cos(b*x + phi) + d
        bounds = ([0, 0, -2*np.pi, -np.inf], [np.inf, np.inf, 2*np.pi, np.inf])
        popt, pcov = optimize.curve_fit(model, x, y, p0=p0, bounds=bounds)
        res = y - model(x, *popt)
        ssq = float((res**2).sum())

        return self._create_fit_result(A=popt[0], b=popt[1], phi=popt[2], d=popt[3],
                                       fitfunc=model, popt=popt.tolist(), pcov=pcov.tolist(),
                                       initial_guess=p0, ssq=ssq)

    def fit_cos_negative(self, xdata, ydata):
        """Bounded negative cosine fit with diagnostics."""
        x = np.array(xdata)
        y = np.array(ydata)
        amp0 = (y.max() - y.min()) / 2
        d0 = y.mean()
        freq0 = 1.0 / (x[-1] - x[0] + 1e-9)
        p0 = [amp0, 2*np.pi*freq0, 0.0, d0]

        def model(x, A, b, phi, d): return -A * np.cos(b*x + phi) + d
        bounds = ([0, 0, -2*np.pi, -np.inf], [np.inf, np.inf, 2*np.pi, np.inf])
        popt, pcov = optimize.curve_fit(model, x, y, p0=p0, bounds=bounds)
        res = y - model(x, *popt)
        ssq = float((res**2).sum())

        return self._create_fit_result(A=popt[0], b=popt[1], phi=popt[2], d=popt[3],
                                       fitfunc=model, popt=popt.tolist(), pcov=pcov.tolist(),
                                       initial_guess=p0, ssq=ssq)

    def _create_fit_result(self, A, b, phi, d, fitfunc, popt, pcov, initial_guess, ssq):
        """Package fit results with amplitude, omega, phase, offset, frequency, period, and diagnostics."""
        freq = b / (2*np.pi)
        period = 1.0 / freq if freq != 0 else float('inf')
        maxcov = float(np.max(pcov)) if pcov else None
        return {
            'amp': float(A),
            'omega': float(b),
            'phase': float(phi),
            'offset': float(d),
            'freq': float(freq),
            'period': float(period),
            'ssq': ssq,
            'maxcov': maxcov,
            'fitfunc': fitfunc,
            'initial_guess': initial_guess,
            'popt': popt,
            'pcov': pcov
        }

    def import_calibration(self, filepath):
        """Import calibration data exported by export_calibration."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        resistance_params = {}
        for key, entry in data.get('resistance_calibration', {}).items():
            pin = entry.get('pin')
            rp = entry.get('resistance_params', {})
            meas = entry.get('measurement_data', {})
            currents_mA = meas.get('currents', [])
            resistance_params[pin] = {
                'a': rp.get('a'),
                'c': rp.get('c'),
                'd': rp.get('d'),
                'rmin_ohm': rp.get('rmin'),
                'rmax_ohm': rp.get('rmax'),
                'alpha': rp.get('alpha'),
                'currents_mA': currents_mA,
                'currents_A': [i/1000.0 for i in currents_mA],
                'voltages_V': meas.get('voltages', []),
                'max_current_mA': meas.get('max_current'),
                'max_current_A': meas.get('max_current', 0)/1000.0,
                'resistance_parameters': {'a': rp.get('a'), 'c': rp.get('c'), 'd': rp.get('d')}
            }

        phase_params = {}
        for key, entry in data.get('phase_calibration', {}).items():
            pin = entry.get('pin')
            pp = entry.get('phase_params', {})
            meas = entry.get('measurement_data', {})
            io_conf = pp.get('io_config')
            fit_func = self.fit_cos if io_conf == 'cross_state' else self.fit_cos_negative
            currents_mA = meas.get('currents', [])
            phase_params[pin] = {
                'io_config': io_conf,
                'amp': pp.get('amplitude'),
                'omega': pp.get('frequency') * 2 * np.pi,
                'phase': pp.get('phase'),
                'offset': pp.get('offset'),
                'powers_mW': meas.get('heating_powers', []),
                'optical_powers': meas.get('optical_powers', []),
                'currents_mA': currents_mA,
                'currents_A': [i/1000.0 for i in currents_mA],
                'fitfunc': fit_func
            }

        return resistance_params, phase_params
    
    def export_calibration(self, resistance_params, phase_params, filepath=None):
        """Export calibration data to JSON format, including full SI‐unit measurements and fit diagnostics."""
        # Generate filepath with timestamp if not provided
        if filepath is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"calibration_data_{timestamp}.json"

        # Load label mapping for human‐readable keys
        from pathlib import Path
        mapping_file = Path(__file__).parent.parent / "qontrol" / "12_mode_mapping.json"
        with open(mapping_file, 'r') as f:
            label_map = json.load(f)

        # Build resistance calibration section
        res_entries = []
        for channel, rp in resistance_params.items():
            # Determine label and type from mapping
            label = None; ch_type = None
            for k, v in label_map.items():
                if 'theta' in v and v['theta'] == int(channel):
                    label, ch_type = k, 'theta'; break
                if 'phi' in v and v['phi'] == int(channel):
                    label, ch_type = k, 'phi'; break
            key = f"{label}_{ch_type}" if label and ch_type else str(channel)

            meas = {
                'currents_mA': rp.get('currents_mA', []),
                'currents_A': rp.get('currents_A', []),
                'voltages_V': rp.get('voltages_V', []),
                'resistances_ohm': rp.get('resistances_ohm', []),
                'max_current_mA': rp.get('max_current_mA'),
                'max_current_A': rp.get('max_current_A')
            }
            params = {
                'a': float(rp['a']),
                'c': float(rp['c']),
                'd': float(rp['d']),
                'rmin': float(rp.get('rmin_ohm', 0.0)),
                'rmax': float(rp.get('rmax_ohm', 0.0)),
                'alpha': float(rp.get('alpha', 0.0)),
                'residuals_ssq': rp.get('residuals_ssq')
            }
            res_entries.append((key, {
                'pin': int(channel),
                'resistance_params': params,
                'measurement_data': meas
            }))
        res_entries.sort(key=lambda x: x[0])
        resistance_data = {k: v for k, v in res_entries}

        # Build phase calibration section
        ph_entries = []
        for channel, pp in phase_params.items():
            label = None; ch_type = None
            for k, v in label_map.items():
                if 'theta' in v and v['theta'] == int(channel):
                    label, ch_type = k, 'theta'; break
                if 'phi' in v and v['phi'] == int(channel):
                    label, ch_type = k, 'phi'; break
            key = f"{label}_{ch_type}" if label and ch_type else str(channel)

            meas = {
                'powers_mW': pp.get('powers_mW', []),
                'currents_mA': pp.get('currents_mA', []),
                'currents_A': pp.get('currents_A', []),
                'optical_powers': pp.get('optical_powers', [])
            }
            params = {
                'io_config': pp.get('io_config'),
                'amplitude': float(pp.get('amp', 0.0)),
                'frequency': float(pp.get('omega', 0.0) / (2 * np.pi)),
                'phase': float(pp.get('phase', 0.0)),
                'offset': float(pp.get('offset', 0.0)),
                'ssq': pp.get('ssq'),
                'maxcov': pp.get('maxcov')
            }
            ph_entries.append((key, {
                'pin': int(channel),
                'phase_params': params,
                'measurement_data': meas
            }))
        ph_entries.sort(key=lambda x: x[0])
        phase_data = {k: v for k, v in ph_entries}

        # Combine into full document
        calibration_data = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'version': '1.0'
            },
            'resistance_calibration': resistance_data,
            'phase_calibration': phase_data
        }

        # Write to JSON
        with open(filepath, 'w') as f:
            json.dump(calibration_data, f, indent=4)

        return filepath

    def calculate_current_for_phase(self, channel, target_phase_pi, resistance_params, phase_params):
        """Calculate current (mA) to achieve target phase shift (in π units) for a channel.
        Args:
            channel: integer channel key matching resistance_params and phase_params dicts
            target_phase_pi: desired phase in multiples of π
            resistance_params: dict of resistance characterization (from import_calibration)
            phase_params: dict of phase characterization (from import_calibration)
        """
        # Get resistance parameters
        res = resistance_params.get(channel)
        if not res:
            raise KeyError(f"Resistance parameters for channel {channel} not found.")
        a = res['resistance_parameters']['a']
        c = res['resistance_parameters']['c']
        R0 = c * 1000.0  # convert kΩ to Ω if c in kΩ, else assume Ω
        alpha = a / c if c != 0 else 0.0

        # Get phase parameters
        ph = phase_params.get(channel)
        if not ph:
            raise KeyError(f"Phase parameters for channel {channel} not found.")
        A = ph['amp']
        omega = ph['omega']  # rad/mW
        phi0 = ph['phase']
        d = ph['offset']
        io_conf = ph.get('io_config', 'cross_state')

        # Convert target phase to rad
        target_phi = target_phase_pi * np.pi
        # Account for bar_state
        sign = 1 if io_conf == 'cross_state' else -1
        # Invert cosine: target_phi = sign*A*cos(omega*P + phi0) + d
        cos_arg = (target_phi - d) / (sign * A)
        cos_arg = np.clip(cos_arg, -1, 1)
        theta = np.arccos(cos_arg)
        # Solve for P_mW: omega*P + phi0 = theta (principal)
        P_mw = (theta - phi0) / omega
        if P_mw < 0:
            P_mw = (2*np.pi - theta - phi0) / omega
        # Convert to Watts
        P_w = P_mw / 1000.0

        # Solve P_w = I^2*R0 + alpha*I^4*R0
        I = sp.symbols('I')
        eq = sp.Eq(alpha * I**4 + I**2 - (P_w / R0), 0)
        sols = sp.solve(eq, I)
        real_pos = [s.evalf() for s in sols if s.is_real and s.evalf() > 0]
        if not real_pos:
            raise ValueError(f"No positive current solution for channel {channel} and phase {target_phase_pi}π.")
        I_A = real_pos[0]
        I_mA = float(I_A * 1000)
        return I_mA
