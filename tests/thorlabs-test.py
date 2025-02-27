import pyvisa
rm = pyvisa.ResourceManager()
print(rm)  # Shows active backend, e.g., <ResourceManager('/usr/lib/visa.so')>
resources = rm.list_resources()
print(f"Detected instruments: {resources}")
