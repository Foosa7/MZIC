from scipy.optimize import curve_fit
import numpy as np
import matplotlib.pyplot as plt


'''
V_PD2 = np.array([3.98, 3.67, 2.93, 2.18, 1.45, 764*1e-3, 141*1e-3])  # millivolts from NI
P_thorlabs = np.array([1.534, 1.277, 1.016, 0.759, 0.508, 265.8*1e3, 48.7*1e3])  # microwatts
'''

# Data
V_PD1 = np.array([743.18, 795.52, 921.14, 989, 1104.3, 1277.1, 1465.5, 1753.4, 2020.3, 2334.3, 2938.85, 3375.9, 3684.7, 3899.3, 3920.3])  # millivolts from NI
V_PD2 = np.array([748.44, 795.55, 921.16, 986.5, 1099.3, 1277.1, 1470.7, 1758.6, 2022.9, 2342.15, 2941.4, 3375.8, 3666.35, 3935.8, 3956.8])  # millivolts from NI
P_thorlabs = np.array([259.1, 277.1, 321.1, 343.1, 384.7, 444.7, 512, 611, 704, 814, 1023, 1179, 1291, 1395, 1527])  # microwatts


# Convert units to Volts and Watts
V_PD1 = V_PD1 / 1000  # V
V_PD2 = V_PD2 / 1000  # V
P_thorlabs = P_thorlabs / 1e6  # W

# Fit function
def model(V, a, b):
    return a * V + b

# Fit both PDs
params1, _ = curve_fit(model, V_PD1, P_thorlabs)
a1, b1 = params1

params2, _ = curve_fit(model, V_PD2, P_thorlabs)
a2, b2 = params2

# Print results
print("Photodiode 1 Fit:  P = a1 * V + b1")
print(f"  a1 = {a1:.4e} W/V")
print(f"  b1 = {b1:.4e} W\n")

print("Photodiode 2 Fit:  P = a2 * V + b2")
print(f"  a2 = {a2:.4e} W/V")
print(f"  b2 = {b2:.4e} W\n")

# Generate fit lines
V_fit = np.linspace(min(V_PD1.min(), V_PD2.min()), max(V_PD1.max(), V_PD2.max()), 200)
P_fit1 = model(V_fit, a1, b1)
P_fit2 = model(V_fit, a2, b2)

# Plot
plt.figure(figsize=(8, 5))
plt.scatter(V_PD1, P_thorlabs, label='PD1 Data', color='blue', marker='o')
plt.scatter(V_PD2, P_thorlabs, label='PD2 Data', color='green', marker='x')
plt.plot(V_fit, P_fit1, label='PD1 Fit', color='blue', linestyle='--')
plt.plot(V_fit, P_fit2, label='PD2 Fit', color='green', linestyle='--')

# Labels and formatting
plt.xlabel('Photodiode Voltage (V)')
plt.ylabel('Optical Power (W)')
plt.title('Photodiode Calibration vs. Thorlabs Power Meter')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()


