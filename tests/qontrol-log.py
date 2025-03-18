from qontrol import QXOutput
import time

# Initialize the device
q = QXOutput(serial_port_name='/dev/ttyUSB0')  # Replace with your actual port

# Alternative: Use built-in print_log method
print("\nLog entries:")
q.print_log(n=10)