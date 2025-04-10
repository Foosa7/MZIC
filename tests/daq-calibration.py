from scipy.optimize import curve_fit
import numpy as np
import matplotlib.pyplot as plt

# Data
V_PDs = {
    "PD1": np.array([4330,  3990,  3540, 2770,  2200, 1780,  1270,  947,  581,  105]),  # millivolts from NI
    "PD2": np.array([4350,  4000,  3540, 2810, 2280, 1780,  1290,  963,  591,  105]),  # millivolts from NI
    "PD3": np.array([4370,  4340,  3560, 3160, 2550, 2010,  1440,  1080,  665,  120]),  # millivolts from NI
    "PD4": np.array([4220, 3810,  3390,  2670, 2115, 1690,  1220,  911,  565,  105]),  # millivolts from NI
    "PD5": np.array([4420, 4380,  3980,  3160, 2550, 1980,  1420,  1060,  654,  120]),  # millivolts from NI
    "PD6": np.array([4360, 4330,  4010,  3180, 2580, 2020,  1455,  1090,  665,  120]),  # millivolts from NI
    "PD7": np.array([4370, 4290,  3850,  3040, 2460, 1930,  1385,  1040,  638,  115]),  # millivolts from NI
    "PD8": np.array([4250, 3820,  3370,  2670, 2180, 1710,  1225,  921,  560,  105]),  # millivolts from NI
}
P_thorlabs = np.array([1710, 1533, 1366, 1074, 868, 683, 490,  369.8,  226.7,  41.55])  # microwatts

# Convert units to Volts and Watts
for key in V_PDs:
    V_PDs[key] = V_PDs[key] / 1000  # Convert millivolts to volts
P_thorlabs = P_thorlabs / 1e6  # Convert microwatts to watts

# Fit function
def model(V, a, b):
    return a * V + b

# Fit each photodiode and store results
fit_results = {}
V_fit = None
for pd_name, V_PD in V_PDs.items():
    if len(V_PD) == 0 or len(P_thorlabs) == 0:
        print(f"Skipping {pd_name} due to missing data.")
        continue

    # Perform curve fitting
    params, _ = curve_fit(model, V_PD, P_thorlabs)
    a, b = params
    fit_results[pd_name] = (a, b)

    # Generate fit lines for plotting
    if V_fit is None:
        V_fit = np.linspace(min(V_PD.min() for V_PD in V_PDs.values() if len(V_PD) > 0),
                            max(V_PD.max() for V_PD in V_PDs.values() if len(V_PD) > 0), 200)

# Plot results
plt.figure(figsize=(10, 6))
for pd_name, (a, b) in fit_results.items():
    V_PD = V_PDs[pd_name]
    P_fit = model(V_fit, a, b)
    plt.scatter(V_PD, P_thorlabs, label=f'{pd_name} Data', marker='o')
    plt.plot(V_fit, P_fit, label=f'{pd_name} Fit: P = {a:.4e} * V + {b:.4e}', linestyle='--')

# Labels and formatting
plt.xlabel('Photodiode Voltage (V)')
plt.ylabel('Optical Power (W)')
plt.title('Photodiode Calibration vs. Thorlabs Power Meter')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# Print fit results
for pd_name, (a, b) in fit_results.items():
    print(f"{pd_name} Fit:  P = a * V + b")
    print(f"  a = {a:.4e} W/V")
    print(f"  b = {b:.4e} W\n")


