#!/usr/bin/env python3
"""
Test script for FFT-based cosine fitting using calibration data
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import optimize

class FFTCosineFitter:
    """Class for FFT-based cosine fitting analysis"""
    
    def __init__(self):
        self.debug = True
    
    def fit_cos_negative(self, xdata, ydata):
        """Negative cosine fit with FFT-based frequency estimation"""
        return self._fit_cosine_general(xdata, ydata, positive=False)
    
    def _fit_cosine_general(self, xdata, ydata, positive=True):
        """General cosine fitting function with FFT-based frequency estimation"""
        xdata = np.array(xdata)
        ydata = np.array(ydata)
        
        # Basic statistics for initial guesses
        guess_offset = np.mean(ydata)
        guess_amp = (np.max(ydata) - np.min(ydata)) / 2
        
        # FFT-based frequency and phase estimation
        guess_freq, fft_phase, fft_details = self._estimate_frequency_phase_fft(
            xdata, ydata, guess_offset, positive
        )
        
        # Build initial guess
        guess = [guess_amp, 2.*np.pi*guess_freq, fft_phase, guess_offset]
        
        if self.debug:
            print(f"\nInitial guess from FFT:")
            print(f"  Amplitude: {guess_amp:.6f}")
            print(f"  Frequency: {guess_freq:.6f} cycles/mW")
            print(f"  Angular freq: {2*np.pi*guess_freq:.6f} rad/mW")
            print(f"  Phase: {fft_phase:.6f} rad ({fft_phase/np.pi:.3f}π)")
            print(f"  Offset: {guess_offset:.6f}")
        
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
            
            if self.debug:
                print(f"\nFit successful!")
                print(f"Final parameters:")
                print(f"  Amplitude: {popt[0]:.6f}")
                print(f"  Angular freq: {popt[1]:.6f} rad/mW")
                print(f"  Frequency: {popt[1]/(2*np.pi):.6f} cycles/mW")
                print(f"  Phase: {popt[2]:.6f} rad ({popt[2]/np.pi:.3f}π)")
                print(f"  Offset: {popt[3]:.6f}")
                
        except Exception as e:
            print(f"Fit failed: {e}")
            raise
        
        # Return fit results and FFT details for analysis
        return {
            'popt': popt,
            'pcov': pcov,
            'fitfunc': cos_func,
            'fft_details': fft_details,
            'guess': guess
        }
    
    def _estimate_frequency_phase_fft(self, xdata, ydata, offset, positive=True):
        """Estimate dominant frequency and phase using FFT with detailed analysis"""
        n = len(xdata)
        
        # Default fallback values
        default_freq = 1/20
        default_phase = 0 if positive else np.pi
        
        fft_details = {
            'frequencies': None,
            'magnitudes': None,
            'phases': None,
            'dominant_freq': default_freq,
            'dominant_phase': default_phase,
            'top_frequencies': []
        }
        
        if n <= 10:
            print("Not enough points for reliable FFT")
            return default_freq, default_phase, fft_details
        
        try:
            # Remove DC component
            ydata_centered = ydata - offset
            
            # Create uniform spacing for FFT
            x_uniform = np.linspace(xdata[0], xdata[-1], n)
            y_uniform = np.interp(x_uniform, xdata, ydata_centered)
            
            # Perform FFT
            fft_vals = np.fft.fft(y_uniform)
            fft_freqs = np.fft.fftfreq(n, d=(x_uniform[1] - x_uniform[0]))
            
            # Get positive frequencies only
            positive_freq_mask = fft_freqs > 0
            pos_freqs = fft_freqs[positive_freq_mask]
            pos_fft_vals = fft_vals[positive_freq_mask]
            pos_magnitudes = np.abs(pos_fft_vals)
            pos_phases = np.angle(pos_fft_vals)
            
            # Store FFT details
            fft_details['frequencies'] = pos_freqs
            fft_details['magnitudes'] = pos_magnitudes
            fft_details['phases'] = pos_phases
            
            # Find top 5 frequencies by magnitude
            top_indices = np.argsort(pos_magnitudes)[-5:][::-1]
            for idx in top_indices:
                fft_details['top_frequencies'].append({
                    'frequency': pos_freqs[idx],
                    'magnitude': pos_magnitudes[idx],
                    'phase': pos_phases[idx]
                })
            
            # Get dominant frequency
            peak_idx = np.argmax(pos_magnitudes)
            dominant_freq = pos_freqs[peak_idx]
            fft_phase = pos_phases[peak_idx]
            
            # Adjust phase for negative cosine
            if not positive:
                fft_phase += np.pi
            
            # Ensure phase is in [-2π, 2π]
            fft_phase = np.arctan2(np.sin(fft_phase), np.cos(fft_phase))
            
            fft_details['dominant_freq'] = dominant_freq
            fft_details['dominant_phase'] = fft_phase
            
            if self.debug:
                print(f"\nFFT Analysis:")
                print(f"  Number of points: {n}")
                print(f"  Frequency resolution: {pos_freqs[1] - pos_freqs[0]:.6f} cycles/mW")
                print(f"  Dominant frequency: {dominant_freq:.6f} cycles/mW")
                print(f"  Dominant phase: {fft_phase:.6f} rad ({fft_phase/np.pi:.3f}π)")
                print(f"\n  Top 5 frequencies:")
                for i, freq_info in enumerate(fft_details['top_frequencies']):
                    print(f"    {i+1}. f={freq_info['frequency']:.6f} cycles/mW, "
                          f"mag={freq_info['magnitude']:.6f}, "
                          f"phase={freq_info['phase']/np.pi:.3f}π")
            
            return abs(dominant_freq), fft_phase, fft_details
            
        except Exception as e:
            print(f"FFT estimation failed: {e}")
            return default_freq, default_phase, fft_details


def plot_fft_analysis(xdata, ydata, fft_details, fit_result):
    """Create comprehensive plots of FFT analysis and fitting results"""
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('FFT-Based Cosine Fitting Analysis', fontsize=16)
    
    # Plot 1: Original data and fit
    ax1 = axes[0, 0]
    ax1.scatter(xdata, ydata, alpha=0.6, label='Data', s=30)
    
    # Generate smooth fit curve
    x_smooth = np.linspace(min(xdata), max(xdata), 500)
    popt = fit_result['popt']
    y_fit = fit_result['fitfunc'](x_smooth, *popt)
    ax1.plot(x_smooth, y_fit, 'r-', linewidth=2, label='Fitted curve')
    
    # Also plot initial guess
    guess = fit_result['guess']
    y_guess = fit_result['fitfunc'](x_smooth, *guess)
    ax1.plot(x_smooth, y_guess, 'g--', alpha=0.5, linewidth=1.5, label='Initial guess (FFT)')
    
    ax1.set_xlabel('Heating Power (mW)')
    ax1.set_ylabel('Optical Power (mW)')
    ax1.set_title('Data and Cosine Fit')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: FFT Spectrum
    ax2 = axes[0, 1]
    if fft_details['frequencies'] is not None:
        ax2.stem(fft_details['frequencies'], fft_details['magnitudes'], 
                 basefmt=' ', markerfmt='o', linefmt='-')
        
        # Highlight dominant frequency
        dom_freq = fft_details['dominant_freq']
        dom_idx = np.argmin(np.abs(fft_details['frequencies'] - dom_freq))
        ax2.plot(dom_freq, fft_details['magnitudes'][dom_idx], 'r*', 
                markersize=15, label=f'Dominant: {dom_freq:.4f} cycles/mW')
        
        ax2.set_xlabel('Frequency (cycles/mW)')
        ax2.set_ylabel('Magnitude')
        ax2.set_title('FFT Frequency Spectrum')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(-0.01, max(fft_details['frequencies'])*1.1)
    
    # Plot 3: Residuals
    ax3 = axes[1, 0]
    y_fit_data = fit_result['fitfunc'](xdata, *popt)
    residuals = ydata - y_fit_data
    ax3.scatter(xdata, residuals, alpha=0.6, s=30)
    ax3.axhline(y=0, color='r', linestyle='--', alpha=0.5)
    ax3.set_xlabel('Heating Power (mW)')
    ax3.set_ylabel('Residuals (mW)')
    ax3.set_title('Fit Residuals')
    ax3.grid(True, alpha=0.3)
    
    # Add RMS error
    rms_error = np.sqrt(np.mean(residuals**2))
    ax3.text(0.05, 0.95, f'RMS Error: {rms_error:.6f} mW', 
             transform=ax3.transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Plot 4: Phase information
    ax4 = axes[1, 1]
    
    # Create text summary
    text_lines = [
        "FFT Analysis Summary:",
        f"Dominant frequency: {fft_details['dominant_freq']:.6f} cycles/mW",
        f"Period: {1/fft_details['dominant_freq']:.3f} mW",
        f"FFT phase: {fft_details['dominant_phase']/np.pi:.3f}π",
        f"",
        "Fit Parameters:",
        f"Amplitude: {popt[0]:.6f} mW",
        f"Frequency: {popt[1]/(2*np.pi):.6f} cycles/mW",
        f"Angular freq: {popt[1]:.6f} rad/mW",
        f"Phase: {popt[2]/np.pi:.3f}π",
        f"Offset: {popt[3]:.6f} mW",
        f"",
        "Comparison:",
        f"Freq ratio (fit/FFT): {(popt[1]/(2*np.pi))/fft_details['dominant_freq']:.3f}",
        f"Phase diff: {(popt[2] - fft_details['dominant_phase'])/np.pi:.3f}π"
    ]
    
    text = '\n'.join(text_lines)
    ax4.text(0.05, 0.95, text, transform=ax4.transAxes, verticalalignment='top',
             fontfamily='monospace', fontsize=10)
    ax4.axis('off')
    
    plt.tight_layout()
    return fig


def main():
    """Main test function"""
    
    # Embedded calibration data
    calibration_data = {
        "resistance_calibration": {
            "A1_theta": {
                "pin": 63,
                "resistance_params": {
                    "a_res": -0.010933101348411911,
                    "c_res": 1.5497787733797306,
                    "d_res": 0.003175702479339366,
                    "rmin": 1.5251792953458039,
                    "rmax": 1.5497787733797306,
                    "alpha_res": -0.007054620656965893
                },
                "measurement_data": {
                    "currents": [
                        0.0,
                        0.16666666666666666,
                        0.3333333333333333,
                        0.5,
                        0.6666666666666666,
                        0.8333333333333333,
                        1.0,
                        1.1666666666666665,
                        1.3333333333333333,
                        1.5
                    ],
                    "voltages": [
                        0.0002,
                        0.2697,
                        0.521,
                        0.7734,
                        1.0273,
                        1.2826,
                        1.5398,
                        1.7988,
                        2.0614,
                        2.2784
                    ],
                    "max_current": 1.5
                }
            }
        },
        "phase_calibration": {
            "A1_theta": {
                "pin": 63,
                "phase_params": {
                    "io_config": "bar",
                    "amplitude": 0.008270759928540728,
                    "omega": 2.5452039899610552,
                    "phase": 0.47676402090686043,
                    "offset": 0.023271400715335847
                },
                "measurement_data": {
                    "currents": [
                    0.0,
                    0.2127972738746409,
                    0.3009836088453302,
                    0.36868062484082276,
                    0.4257763908089212,
                    0.4761003808178984,
                    0.5216162962401464,
                    0.5634904996526137,
                    0.6024828341060965,
                    0.6391210150698289,
                    0.6737892160616548,
                    0.7067774174385189,
                    0.7383108745448855,
                    0.7685686970133677,
                    0.7976960868288194,
                    0.8258126953554747,
                    0.8530185052887145,
                    0.8793980785002502,
                    0.9050236925748376,
                    0.929957701968643,
                    0.9542543459272983,
                    0.9779611537947751,
                    1.0011200521496508,
                    1.0237682476245462,
                    1.0459389385723143,
                    1.0676618944644027,
                    1.0889639318787256,
                    1.109869308776482,
                    1.1304000535833643,
                    1.1505762417849337,
                    1.1704162299177951,
                    1.1899368547118505,
                    1.209153603524169,
                    1.2280807609657134,
                    1.2467315356630007,
                    1.2651181703480132,
                    1.2832520378800087,
                    1.3011437253357545,
                    1.3188031079314975,
                    1.3362394142399914,
                    1.3534612839234907,
                    1.3704768190061696,
                    1.3872936295481433,
                    1.4039188744503732,
                    1.4203592980101998,
                    1.4366212627560828,
                    1.4527107790140732,
                    1.4686335315950507,
                    1.4843949039380677,
                    1.4999999999999998
                    ],
                    "optical_powers": [
                    0.022149102700000003,
                    0.0237823479,
                    0.0252907266,
                    0.0267082869,
                    0.027983951400000002,
                    0.0291475153,
                    0.0301053278,
                    0.0307935334,
                    0.0312249031,
                    0.031403695200000005,
                    0.031283081600000005,
                    0.030887185900000003,
                    0.0302145909,
                    0.029370296,
                    0.0282592318,
                    0.0269750562,
                    0.025529116100000002,
                    0.024009385,
                    0.0224811447,
                    0.0210110793,
                    0.0196602086,
                    0.0183646807,
                    0.0172294949,
                    0.016294387,
                    0.015596248,
                    0.0151819058,
                    0.0150343321,
                    0.0151492677,
                    0.015516785399999998,
                    0.016128366,
                    0.0169811719,
                    0.0180624356,
                    0.0192969492,
                    0.0206776203,
                    0.0221476821,
                    0.023636192099999998,
                    0.0251275433,
                    0.026511048399999997,
                    0.02779239,
                    0.0289360887,
                    0.0299265357,
                    0.030680013899999997,
                    0.0311539552,
                    0.0313370037,
                    0.0311936856,
                    0.0313313249,
                    0.0311766562,
                    0.030716906600000003,
                    0.0300003248,
                    0.0291035267
                    ]
                }
            }
        }
    }
    
    # Extract phase calibration data for A1_theta
    phase_cal = calibration_data['phase_calibration']['A1_theta']
    measurement_data = phase_cal['measurement_data']
    
    # Calculate heating powers from currents using resistance data
    resistance_cal = calibration_data['resistance_calibration']['A1_theta']
    res_params = resistance_cal['resistance_params']
    a_res = res_params['a_res']
    c_res = res_params['c_res']
    
    currents = np.array(measurement_data['currents'])
    optical_powers = np.array(measurement_data['optical_powers'])
    
    # Calculate heating power: P = I²R where R = aI² + c
    resistances = a_res * currents**2 + c_res
    heating_powers = currents**2 * resistances  # P = I²R in mW
    
    print("="*60)
    print("FFT-BASED COSINE FITTING TEST")
    print("="*60)
    print(f"\nData info:")
    print(f"  Number of points: {len(currents)}")
    print(f"  Current range: {min(currents):.3f} - {max(currents):.3f} mA")
    print(f"  Power range: {min(heating_powers):.3f} - {max(heating_powers):.3f} mW")
    print(f"  Optical power range: {min(optical_powers):.6f} - {max(optical_powers):.6f} mW")
    print(f"  IO Config: {phase_cal['phase_params']['io_config']}")
    
    # Create fitter and perform analysis
    fitter = FFTCosineFitter()
    
    # Since io_config is "bar", we use negative cosine fit
    fit_result = fitter.fit_cos_negative(heating_powers, optical_powers)
    
    # Compare with stored parameters
    print("\n" + "="*60)
    print("COMPARISON WITH STORED PARAMETERS:")
    print("="*60)
    stored_params = phase_cal['phase_params']
    popt = fit_result['popt']
    
    print(f"\nAmplitude:")
    print(f"  Stored: {stored_params['amplitude']:.6f}")
    print(f"  Fitted: {popt[0]:.6f}")
    print(f"  Difference: {abs(stored_params['amplitude'] - popt[0]):.6f}")
    
    print(f"\nAngular frequency (omega):")
    print(f"  Stored: {stored_params['omega']:.6f} rad/mW")
    print(f"  Fitted: {popt[1]:.6f} rad/mW")
    print(f"  Difference: {abs(stored_params['omega'] - popt[1]):.6f}")
    
    print(f"\nPhase:")
    print(f"  Stored: {stored_params['phase']:.6f} rad ({stored_params['phase']/np.pi:.3f}π)")
    print(f"  Fitted: {popt[2]:.6f} rad ({popt[2]/np.pi:.3f}π)")
    print(f"  Difference: {abs(stored_params['phase'] - popt[2]):.6f} rad")
    
    print(f"\nOffset:")
    print(f"  Stored: {stored_params['offset']:.6f}")
    print(f"  Fitted: {popt[3]:.6f}")
    print(f"  Difference: {abs(stored_params['offset'] - popt[3]):.6f}")
    
    # Create visualization
    fig = plot_fft_analysis(heating_powers, optical_powers, 
                           fit_result['fft_details'], fit_result)
    
    plt.savefig('fft_analysis_results.png', dpi=150, bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    main()