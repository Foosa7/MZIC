import json
import os
import argparse
import numpy as np
import sympy as sp
import matplotlib.pyplot as plt


def get_calibration_data(data, key_name):
    """
    Retrieve calibration section for a given key from loaded JSON.
    """
    for suffix in ['', '_data']:
        section = f"{key_name}_calibration{suffix}" if suffix else f"{key_name}_calibration"
        if section in data:
            return data[section]
    return None


def plot_resistance(res_cal, title=None):
    """
    Plot voltage vs. current for each resistance calibration channel.
    """
    channels = list(res_cal.keys())
    fig, axes = plt.subplots(len(channels), 1, figsize=(8, 4 * len(channels)))
    if len(channels) == 1:
        axes = [axes]
    for ax, ch in zip(axes, channels):
        md = res_cal[ch].get('measurement_data', {})
        I = np.array(md.get('currents', []))
        V = np.array(md.get('voltages', []))
        if I.size and V.size:
            ax.plot(I, V, 'o-', label=ch)
            ax.set_xlabel('Current (mA)')
            ax.set_ylabel('Voltage (V)')
            ax.grid(True)
        else:
            ax.text(0.5, 0.5, 'No data', ha='center')
        ax.set_title(ch)
    if title:
        fig.suptitle(title)
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig


def plot_phase(ph_cal, res_cal, title=None):
    """
    Plot optical power vs. electrical power and optical vs. current for phase calibration.
    """
    channels = list(ph_cal.keys())
    fig, axes = plt.subplots(len(channels), 2, figsize=(12, 4 * len(channels)))
    if len(channels) == 1:
        axes = np.array([axes])
    for i, ch in enumerate(channels):
        md = ph_cal[ch].get('measurement_data', {})
        I_mA = np.array(md.get('currents', []))
        O_uW = np.array(md.get('optical_powers', []))

        c_res = res_cal[ch]['resistance_params']['c_res']
        R0 = c_res * 1000.0
        I_A = I_mA / 1000.0
        P_mW = (I_A ** 2) * R0 * 1000.0

        ax1 = axes[i, 0]
        if P_mW.size and O_uW.size:
            ax1.plot(P_mW, O_uW, 'o-')
            ax1.set_xlabel('Power (mW)')
            ax1.set_ylabel('Optical (uW)')
            ax1.grid(True)
        else:
            ax1.text(0.5, 0.5, 'No data', ha='center')
        ax1.set_title(f"{ch} Optical vs. Power")

        ax2 = axes[i, 1]
        if I_mA.size and O_uW.size:
            ax2.plot(I_mA, O_uW, 'o-')
            ax2.set_xlabel('Current (mA)')
            ax2.set_ylabel('Optical (uW)')
            ax2.grid(True)
        else:
            ax2.text(0.5, 0.5, 'No data', ha='center')
        ax2.set_title(f"{ch} Optical vs. Current")

    if title:
        fig.suptitle(title)
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig


        # amplitude: 0.0908441893692287, omega: 0.2762131249289536, phase offset: 3.1415926535897927, offset: 0.09066978105949058 for channel 21
        # r_params[1]: 1008.6807070542391
        #              1036.6441840655363
        # r_params[0]: 3419549.948304372
                    #    3621062.146585479
        # A = params['amp']
        # b = params['omega']
        # c = params['phase']     # offset phase in radians
        # d = params['offset']
        # r_params[1] = c_res
        # r_params[0] = a_res

def calculate_current_for_phase(data, channel, phase_value):
    """
    Compute the current (mA) to reach target phase (in units of π) using linear model.
    """
    res_data = get_calibration_data(data, 'resistance')
    ph_data = get_calibration_data(data, 'phase')
    if channel not in res_data or channel not in ph_data:
        raise KeyError(f"Channel '{channel}' not found in calibration.")

    c_res = (res_data[channel]['resistance_params']['c_res']) * 1000
    a_res = (res_data[channel]['resistance_params']['a_res']) * 10e9   
    A = ph_data[channel]['phase_params']['amplitude'] 
    b = ph_data[channel]['phase_params']['omega']
    c = ph_data[channel]['phase_params']['phase']
    d = ph_data[channel]['phase_params']['offset']

    # c_res = 1036.6441840655363
    # a_res = 3621062.146585479 
    # A = 0.6005338378507308
    # b = 0.2583951254144626
    # c = 0.4247100614593249 #3.1415926535897927
    # d = 0.6021712385768999
    

        # amplitude: 0.0908441893692287, omega: 0.2762131249289536, phase offset: 3.1415926535897927, offset: 0.09066978105949058 for channel 21
        # r_params[1]: 1008.6807070542391
        # r_params[0]: 3419549.948304372
    if phase_value < c/np.pi:
        print(f"Warning: Phase {phase_value}π is less than offset phase {c/np.pi}π for channel {channel}")
        phase_value = phase_value + 2
        print(f"Using adjusted phase value: {phase_value}π")

    # Calculate heating power for this phase shift
    P = abs((phase_value*np.pi - c) / b)
        

    # Define symbols for solving equation
    I = sp.symbols('I')
    P_watts = P/1000  # Convert to watts
    R0 = c_res  # Linear resistance term (c)
    alpha = a_res/R0 if R0 != 0 else 0  # Nonlinearity parameter (a/c)
    
    # Define equation: P/R0 = I^2 + alpha*I^4
    eq = sp.Eq(P_watts/R0, I**2 + alpha*I**4)
    
    # Solve the equation
    solutions = sp.solve(eq, I)

    # Filter and choose the real, positive solution
    positive_solutions = [sol.evalf() for sol in solutions if sol.is_real and sol.evalf() > 0]
    if positive_solutions:
        return float(1000 * positive_solutions[0])  # Convert to mA 
    else:
        # Fallback to linear model
        print(f"error")




    # R0 = c_res * 1000.0

    # ph = ph_data[channel_key]['phase_params']
    # f = ph['omega']
    # phi0 = ph['phase']
    # io_conf = ph.get('io_config', 'cross_state')

    # target_phi = target_phase_pi * np.pi
    # if io_conf == 'cross_state':
    #     target_phi_eff = np.pi - target_phi
    # else:
    #     target_phi_eff = target_phi

    # b = f
    # P_mW = abs((target_phi_eff - phi0) / b)
    # P_W = P_mW / 1000.0

    # a_res = res_data[channel_key]['resistance_params']['a']
    # alpha = a_res / c_res

    # if alpha == 0:
    #     I_A = np.sqrt(P_W / R0)
    # else:
    #     I = sp.symbols('I', real=True, positive=True)
    #     eq = sp.Eq(alpha * I**4 + I**2 - (P_W / R0), 0)
    #     sols = sp.solve(eq, I)
    #     sol = [s.evalf() for s in sols if s.is_real and s > 0]
    #     if not sol:
    #         raise RuntimeError("No valid current solution.")
    #     I_A = sol[0]

    # return float(I_A * 1000.0)

# Demo & CLI entry point
if __name__ == '__main__':
    # --- Demo usage (uncomment to run) ---
    fp = r"c:\Users\hp-ma\Downloads\New Calibration\G4.json"
    with open(fp) as f:
        data = json.load(f)
    for target in [0, 0.5, 1, 2]:
        I_req = calculate_current_for_phase(data, 'G4_theta', target)
        print(f"Target {target}π → {I_req:.3f} mA")
    plot_resistance(get_calibration_data(data, 'resistance'), title="Resistance Calibration")
    plot_phase(get_calibration_data(data, 'phase'), get_calibration_data(data, 'resistance'), title="Phase Calibration")
    plt.show()

    # # --- CLI usage ---
    # parser = argparse.ArgumentParser(description="Plot calibrations and compute phase currents.")
    # parser.add_argument('json_file', nargs='?', help="Path to calibration JSON file")
    # parser.add_argument('--channel', '-c', help="Channel key for current calculation")
    # parser.add_argument('--phases', '-p', nargs='+', type=float,
    #                     help="Target phases (in π units), e.g. 0 0.5 1.0")
    # args = parser.parse_args()

    # if args.json_file:
    #     with open(args.json_file) as f:
    #         data = json.load(f)
    #     res_cal = get_calibration_data(data, 'resistance')
    #     ph_cal = get_calibration_data(data, 'phase')
    #     if res_cal:
    #         plot_resistance(res_cal, title="Resistance Calibration")
    #     if ph_cal and res_cal:
    #         plot_phase(ph_cal, res_cal, title="Phase Calibration")
    #     plt.show()

    #     if args.channel and args.phases:
    #         for t in args.phases:
    #             try:
    #                 I_req = calculate_current_for_phase(data, args.channel, t)
    #                 print(f"Target phase {t}π => Current: {I_req:.3f} mA")
    #             except Exception as e:
    #                 print(f"Error for phase {t}π: {e}")
    # else:
    #     print("No JSON file provided. For demo, uncomment the demo block in the code.")


# def cosfunc(x, A, b, c, d):
#     return A * np.cos(b * x + c) + d


# def fit_cos(xdata, ydata):
#     x = np.array(xdata)
#     y = np.array(ydata)
#     A_guess = (np.max(y) - np.min(y)) / 2
#     b_guess = 2 * np.pi / (x[-1] - x[0])
#     c_guess = 0
#     d_guess = np.mean(y)
#     try:
#         popt, _ = curve_fit(cosfunc, x, y, p0=[A_guess, b_guess, c_guess, d_guess])
#         return {'amp': popt[0], 'frequency': popt[1] / (2 * np.pi), 'phase': popt[2], 'offset': popt[3], 'fit_function': lambda xx: cosfunc(xx, *popt)}
#     except RuntimeError:
#         print("Cosine fitting failed.")
#         return None


# def fit_cos_negative(xdata, ydata):
#     return fit_cos(xdata, -np.array(ydata))


# def get_calibration_data(data, key_name):
#     if f'{key_name}_calibration' in data:
#         return data[f'{key_name}_calibration']
#     if f'{key_name}_calibration_data' in data:
#         return data[f'{key_name}_calibration_data']
#     return None


# def plot_calibration_data(file_path):
#     if not os.path.exists(file_path):
#         print(f"Error: File not found: {file_path}")
#         return
#     with open(file_path, 'r') as f:
#         data = json.load(f)

#     # Resistance calibration plots (voltage vs current)
#     res_cal = get_calibration_data(data, 'resistance')
#     if res_cal:
#         n = len(res_cal)
#         fig_res, axs_res = plt.subplots(n, 1, figsize=(8, 4*n), squeeze=False)
#         fig_res.suptitle(f"Resistance Calibration: V vs I ({os.path.basename(file_path)})")
#         for i, (ch, cal) in enumerate(res_cal.items()):
#             md = cal.get('measurement_data', {})
#             I = md.get('currents'); V = md.get('voltages')
#             ax = axs_res[i,0]
#             if I and V:
#                 ax.plot(I, V, 'o-')
#                 ax.set_title(ch)
#                 ax.set_xlabel('Current (mA)'); ax.set_ylabel('Voltage (V)')
#                 ax.grid(True)
#             else:
#                 ax.text(0.5, 0.5, 'No data', ha='center')
#         plt.tight_layout(rect=[0,0.03,1,0.95])

#     # Phase calibration plots
#     ph_cal = get_calibration_data(data, 'phase')
#     if ph_cal and res_cal:
#         n = len(ph_cal)
#         fig_ph, axs_ph = plt.subplots(n, 2, figsize=(12, 4*n), squeeze=False)
#         fig_ph.suptitle(f"Phase Calibration: Electrical & Optical ({os.path.basename(file_path)})")
#         for i, (ch, cal) in enumerate(ph_cal.items()):
#             md = cal.get('measurement_data', {})
#             I = md.get('currents'); O = md.get('optical_powers')
#             # Electrical power
#             Rs = res_cal[ch]['resistance_params'].get('c',0)*1000
#             I_A = np.array(I)/1000 if I else None
#             P = (I_A**2)*Rs if I_A is not None else None
#             # Fit config
#             io_conf = cal.get('phase_params',{}).get('io_config','cross_state')
#             ax1 = axs_ph[i,0]
#             if P is not None and O:
#                 # Choose fit
#                 if io_conf=='cross_state': fr = fit_cos(P, O)
#                 else: fr = fit_cos_negative(P, O)
#                 ax1.plot(P, O, 'o', label='Data')
#                 if fr:
#                     PF = np.linspace(P.min(),P.max(),400)
#                     ax1.plot(PF, fr['fit_function'](PF),'--',label='Fit')
#                 ax1.set_xlabel('Power (mW)'); ax1.set_ylabel('Optical (uW)')
#                 ax1.set_title(f"{ch} [{io_conf}]")
#                 ax1.legend(); ax1.grid(True)
#             else:
#                 ax1.text(0.5,0.5,'Insufficient',ha='center')
#             # Plot optical vs current
#             ax2 = axs_ph[i,1]
#             if I and O:
#                 ax2.plot(I, O, 'o-')
#                 ax2.set_xlabel('Current (mA)'); ax2.set_ylabel('Optical (uW)')
#                 ax2.set_title(f"{ch}: O vs I")
#                 ax2.grid(True)
#             else:
#                 ax2.text(0.5,0.5,'No data',ha='center')
#         plt.tight_layout(rect=[0,0.03,1,0.95])

#     plt.show()

# def calculate_current_for_phase(data, channel_key, target_phase_pi):
#     """
#     Calculates the required current (mA) to achieve a target phase shift (in π units)
#     for a given channel, using the linear phase model: Phase(P) = b*P + c.
#     """
#     print(f"Calculating Current for Channel: {channel_key}, Target: {target_phase_pi}π")

#     # Load calibration data
#     res_data = get_calibration_data(data, 'resistance')
#     phase_data = get_calibration_data(data, 'phase')
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
#     b_param = ph_params.get('frequency')  # in cycles per mW
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
#     if io_conf == 'bar_state':
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


# if __name__=='__main__':
#     fp = r"c:\Users\hp-ma\Downloads\calibration\A1-test.json"
#     with open(fp) as f:
#         d = json.load(f)
#     # Example calls for different phases
#     for target in [0, 0.5, 1, 2]:
#         calculate_current_for_phase(d, 'K3_theta', target)
#     # Plot data
#     plot_calibration_data(fp)




# # if __name__ == '__main__':
# #     # Example usage
# #     # file_to_plot = r"c:\Users\hp-ma\Downloads\calibration\G1-test-son.json"

# #     fp = r"c:\Users\hp-ma\Downloads\calibration\G1-test-son.json"
# #     with open(fp) as f:
# #         d = json.load(f)
# #     curr = calculate_current_for_phase(d, 'D4_theta', 3)
# #     print(f"Result: {curr} mA")
# #     plot_calibration_data(fp)



#     # plot_calibration_data(file_to_plot)
#     # curr = calculate_current_for_phase(file_to_plot, 'D4_theta', 2)
#     # print(f"Result: {curr} mA")


