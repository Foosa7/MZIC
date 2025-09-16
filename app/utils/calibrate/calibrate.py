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
        # while True:
        #     try:
        #         user_input = input(f"Enter max current for resistance sweep (mA) [Device limit: {qontrol.globalcurrrentlimit} mA]: ")
        #         if not user_input:  # If user just presses enter, use device limit
        #             end_current = qontrol.globalcurrrentlimit
        #             print(f"Using device limit: {end_current} mA")
        #             break
        #         else:
        #             end_current = float(user_input)
        #             if 0 < end_current <= qontrol.globalcurrrentlimit:
        #                 print(f"Using max current: {end_current} mA")
        #                 break
        #             else:
        #                 print(f"Error: Value must be between 0 and {qontrol.globalcurrrentlimit} mA")
        #     except ValueError:
        #         print("Error: Please enter a valid number")
        # start_current = 0
        # steps = 10
        # currents = np.linspace(start_current, end_current, steps).astype(float)
        # voltages = []

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
        
        # # Ask user for max current via terminal
        # while True:
        #     try:
        #         user_input = input(f"Enter max current for phase sweep (mA) [Device limit: {qontrol.globalcurrrentlimit} mA]: ")
        #         if not user_input:  # If user just presses enter, use device limit
        #             max_current = qontrol.globalcurrrentlimit
        #             print(f"Using device limit: {max_current} mA")
        #             break
        #         else:
        #             max_current = float(user_input)
        #             if 0 < max_current <= qontrol.globalcurrrentlimit:
        #                 print(f"Using max current: {max_current} mA")
        #                 break
        #             else:
        #                 print(f"Error: Value must be between 0 and {qontrol.globalcurrrentlimit} mA")
        #     except ValueError:
        #         print("Error: Please enter a valid number")

        # start_current = 0
        # end_current = qontrol.globalcurrrentlimit
        # steps = 50
        # currents = np.linspace(start_current, end_current, steps).astype(float)
        # voltages = []

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
        # Reset current to zero
        qontrol.set_current(channel, 0.0)

        # Use heating power as x-data instead of current
        # Perform cosine fit with power data
        if io_config == "cross":
            fit_result = self.fit_cos(heating_powers_mw, optical_powers)
            logging.info(f"Using positive cosine fit for io_config={io_config}")
        else:
            fit_result = self.fit_cos_negative(heating_powers_mw, optical_powers)
            logging.info(f"Using negative cosine fit for io_config={io_config}")

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
        """Positive cosine fit with FFT-based frequency estimation"""
        return self._fit_cosine_general(xdata, ydata, positive=True)

    def fit_cos_negative(self, xdata, ydata):
        """Negative cosine fit with FFT-based frequency estimation"""
        return self._fit_cosine_general(xdata, ydata, positive=False)

    def _fit_cosine_general(self, xdata, ydata, positive=True):
        """General cosine fitting function with FFT-based frequency estimation
        
        Args:
            xdata: Array of x values (heating power in mW)
            ydata: Array of y values (optical power in mW)
            positive: If True, fits A*cos(bx+c)+d; if False, fits -A*cos(bx+c)+d
        
        Returns:
            Dictionary with fit results
        """
        xdata = np.array(xdata)
        ydata = np.array(ydata)
        
        # Basic statistics for initial guesses
        guess_offset = np.mean(ydata)
        guess_amp = (np.max(ydata) - np.min(ydata)) / 2
        
        # FFT-based frequency and phase estimation
        guess_freq, fft_phase = self._estimate_frequency_phase_fft(
            xdata, ydata, guess_offset, positive
        )
        
        # Build initial guess
        guess = [guess_amp, 2.*np.pi*guess_freq, fft_phase, guess_offset]
        
        # Define the cosine function based on sign
        if positive:
            def cos_func(P, A, b, c, d):
                return A * np.cos(b*P + c) + d
        else:
            def cos_func(P, A, b, c, d):
                return -A * np.cos(b*P + c) + d
        
        # Perform curve fitting
        try:
            popt, pcov = optimize.curve_fit(
                cos_func, xdata, ydata, p0=guess,
                bounds=([0, 0, -2*np.pi, -np.inf], [np.inf, np.inf, 2*np.pi, np.inf]),
                maxfev=5000
            )
            logging.info(f"Fit successful with FFT-based guess ({'positive' if positive else 'negative'} cosine)")
        except Exception as e:
            logging.info(f"Fit failed with FFT guess: {e}")
            # Could add fallback strategy here
            raise
        
        A, b, c, d = popt
        
        # Normalize phase to [-π, π] then convert to [-1, 1]
        c_normalized = np.arctan2(np.sin(c), np.cos(c)) / np.pi
        
        logging.info(f"Final parameters: A={A:.4f}, ω={b:.4f}, φ={c_normalized:.4f}π, d={d:.4f}")
        
        return self._create_fit_result(A, b, c_normalized, d, cos_func, popt, pcov, guess)

    def _estimate_frequency_phase_fft(self, xdata, ydata, offset, positive=True):
        """Estimate dominant frequency and phase using FFT
        
        Args:
            xdata: Array of x values
            ydata: Array of y values
            offset: DC offset to remove
            positive: Whether fitting positive or negative cosine
            
        Returns:
            Tuple of (frequency, phase) estimates
        """
        n = len(xdata)
        
        # Default fallback values
        default_freq = 1/20
        default_phase = 0 if positive else np.pi
        
        if n <= 10:  # Not enough points for reliable FFT
            return default_freq, default_phase
        
        try:
            # Remove DC component
            ydata_centered = ydata - offset
            
            # Create uniform spacing for FFT (interpolate if needed)
            x_uniform = np.linspace(xdata[0], xdata[-1], n)
            y_uniform = np.interp(x_uniform, xdata, ydata_centered)
            
            # Perform FFT
            fft_vals = np.fft.fft(y_uniform)
            fft_freqs = np.fft.fftfreq(n, d=(x_uniform[1] - x_uniform[0]))
            
            # Find dominant frequency (exclude DC component at index 0)
            positive_freq_indices = np.where(fft_freqs > 0)[0]
            
            if len(positive_freq_indices) == 0:
                return default_freq, default_phase
            
            # Get magnitudes for positive frequencies
            positive_fft_mags = np.abs(fft_vals[positive_freq_indices])
            
            # Find peak frequency
            peak_idx = np.argmax(positive_fft_mags)
            dominant_freq_idx = positive_freq_indices[peak_idx]
            dominant_freq = fft_freqs[dominant_freq_idx]
            
            # Get phase from FFT
            fft_phase = np.angle(fft_vals[dominant_freq_idx])
            
            # Adjust phase for negative cosine
            if not positive:
                fft_phase += np.pi
            
            # Ensure phase is in [-2π, 2π] for the bounds
            fft_phase = np.arctan2(np.sin(fft_phase), np.cos(fft_phase))
            
            logging.info(f"FFT detected frequency: {dominant_freq:.4f} cycles/mW")
            logging.info(f"FFT detected phase: {fft_phase:.4f} rad ({'positive' if positive else 'negative'} cosine)")
            
            return abs(dominant_freq), fft_phase
            
        except Exception as e:
            logging.info(f"FFT estimation failed: {e}")
            return default_freq, default_phase

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

    def export_calibration(self, resistance_params, phase_params, filepath=None, grid_size='8x8'):
        """Export calibration data to JSON format"""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"calibration_data_{timestamp}.json"

        # Load label mapping from the appropriate grid size
        create_label_mapping, apply_grid_mapping = get_mapping_functions(grid_size)
        label_map = create_label_mapping(int(grid_size.split('x')[0]))

        # Check if data is already in AppData format (with keys like "A1_theta")
        # or in raw calibration format (with integer keys)
        if isinstance(resistance_params, dict) and any(isinstance(k, str) and '_' in k for k in resistance_params.keys()):
            # Already in AppData format - use directly
            resistance_data = resistance_params
            phase_data = phase_params
        else:
            # Convert from raw calibration format (integer keys) to labeled format
            resistance_entries = []
            for channel, params in resistance_params.items():
                # Find the label for this channel
                label = None
                channel_type = None
                for k, v in label_map.items():
                    if v.get("theta") == int(channel):
                        label = k
                        channel_type = "theta"
                        break
                    elif v.get("phi") == int(channel):
                        label = k
                        channel_type = "phi"
                        break
                
                key = f"{label}_{channel_type}" if label and channel_type else str(channel)
                
                # Check if data is nested (from AppData) or flat (from calibration)
                if 'resistance_params' in params:
                    # Nested structure from AppData
                    resistance_entries.append((key, params))
                else:
                    # Flat structure from direct calibration
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

            # Sort by label alphabetically
            resistance_entries.sort(key=lambda x: x[0])
            resistance_data = {k: v for k, v in resistance_entries}

            # Convert phase data
            phase_entries = []
            for channel, params in phase_params.items():
                # Find the label for this channel
                label = None
                channel_type = None
                for k, v in label_map.items():
                    if v.get("theta") == int(channel):
                        label = k
                        channel_type = "theta"
                        break
                    elif v.get("phi") == int(channel):
                        label = k
                        channel_type = "phi"
                        break
                
                key = f"{label}_{channel_type}" if label and channel_type else str(channel)
                
                # Check if data is nested or flat
                if 'phase_params' in params:
                    # Nested structure from AppData
                    phase_entries.append((key, params))
                else:
                    # Flat structure from direct calibration
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
                            "heating_powers": params.get('heating_powers', params.get('currents', [])),
                            "optical_powers": params['optical_powers']
                        }
                    }))

            # Sort by label alphabetically
            phase_entries.sort(key=lambda x: x[0])
            phase_data = {k: v for k, v in phase_entries}

        # Combine all calibration data
        calibration_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "version": "2.0",
                "grid_size": grid_size
            },
            "resistance_calibration": resistance_data,
            "phase_calibration": phase_data
        }

        # Save to file
        with open(filepath, 'w') as f:
            json.dump(calibration_data, f, indent=4)

        return filepath


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
            
            # Get calibration data sections
            resistance_data = data.get('resistance_calibration', {})
            phase_data = data.get('phase_calibration', {})
            
            # Clear existing calibration data in AppData
            AppData.resistance_calibration_data.clear()
            AppData.phase_calibration_data.clear()
            
            # Import resistance data directly to AppData
            for key, params in resistance_data.items():
                AppData.resistance_calibration_data[key] = params
            
            # Import phase data directly to AppData
            for key, params in phase_data.items():
                AppData.phase_calibration_data[key] = params
            
            logging.info(f"Successfully imported calibration data from {filepath}")
            logging.info(f"Loaded {len(resistance_data)} resistance and {len(phase_data)} phase calibrations")
            
            # Return the data for backward compatibility
            return resistance_data, phase_data
            
        except FileNotFoundError:
            logging.error(f"File not found - {filepath}")
            return None, None
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON format - {str(e)}")
            return None, None
        except Exception as e:
            logging.error(f"Failed to import calibration data: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, None
