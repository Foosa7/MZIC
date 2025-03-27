from scipy.optimize import curve_fit
import numpy as np
import matplotlib.pyplot as plt

# Example data
V_PD = np.array([1.37, 1.96, 2.65, 3.27, 3.94])  # volts from NI
P_thorlabs = np.array([1.25e-6, 1.58e-6, 2.23e-6, 2.74e-6, 3.34e-6])  # watts
# Fit function
def model(V, a, b):
    return a * V + b

params, _ = curve_fit(model, V_PD, P_thorlabs)
a, b = params

# Now you can do: P_opt = a * V_PD + b
print(f"Fitted parameters: a = {a}, b = {b}")

# Plotting the data points
plt.scatter(V_PD, P_thorlabs, label='Data Points', color='blue')

# Plotting the fitted curve
V_fit = np.linspace(min(V_PD), max(V_PD), 100)
P_fit = model(V_fit, a, b)
plt.plot(V_fit, P_fit, label='Fitted Curve', color='red')

# Adding labels and legend
plt.xlabel('Voltage (V)')
plt.ylabel('Power (W)')
plt.title('Power vs. Voltage Fitting')
plt.legend()

# Show the plot
plt.show()

a = 8.29084065230446e-07
b = 4.0876234169585323e-08
V_pd = 4.66
P_pd = a*V_pd + b
print(P_pd)