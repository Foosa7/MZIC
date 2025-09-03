# main.py
from app.imports import *
from app.utils.utils import import_pickle
import ctypes
from nidaqmx.errors import DaqNotFoundError 
from app.devices.switch_device import Switch
import serial.tools.list_ports

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "config", "settings.json")

def initialize_switch(port=None, switch_name="Switch"):
    """Initialize switch device with auto-detection or specified port"""
    if port:
        try:
            switch = Switch(port)
            # Test connection
            channel = switch.get_channel()
            if channel is not None:
                logging.info(f"[{switch_name}] Connected to {port}, current channel: {channel}")
                return switch
        except Exception as e:
            logging.error(f"[{switch_name}] Failed to connect to {port}: {e}")
            return None
    else:
        # Auto-detect switch
        ports = serial.tools.list_ports.comports()
        for port_info in ports:
            try:
                switch = Switch(port_info.device)
                channel = switch.get_channel()
                if channel is not None:
                    logging.info(f"[{switch_name}] Auto-detected on {port_info.device}")
                    return switch
            except:
                continue
        logging.warning(f"[{switch_name}] No switch device detected")
        return None

def initialize_dual_switches(config):
    """Initialize both input and output switches based on configuration"""
    # Get switch ports from config or use defaults
    input_port = config.get("switch_input_port", None)
    output_port = config.get("switch_output_port", None)
    
    switch_input = None
    switch_output = None
    used_ports = []  # Track which ports are already in use
    
    # If ports are not specified in config, try to auto-detect
    if not input_port and not output_port:
        logging.info("Auto-detecting switches...")
        ports = serial.tools.list_ports.comports()
        available_ports = [p.device for p in ports]
        
        # Common port patterns for switches
        switch_ports = []
        for port in available_ports:
            if "COM" in port or "ttyUSB" in port or "tty.usbserial" in port:
                switch_ports.append(port)
        
        logging.info(f"Found potential switch ports: {switch_ports}")
        
        # Try to assign switches to available ports
        for port in switch_ports:
            if port in used_ports:
                continue
                
            # Try to connect to this port
            try:
                test_switch = Switch(port)
                channel = test_switch.get_channel()
                if channel is not None:
                    # Successfully connected
                    if not switch_output:  # Assign first working port to output
                        switch_output = test_switch
                        used_ports.append(port)
                        logging.info(f"[Output Switch] Connected to {port}, current channel: {channel}")
                    elif not switch_input:  # Assign second working port to input
                        switch_input = test_switch
                        used_ports.append(port)
                        logging.info(f"[Input Switch] Connected to {port}, current channel: {channel}")
                    else:
                        # Both switches assigned, close this connection
                        test_switch = None
                        break
            except Exception as e:
                logging.error(f"Failed to connect to {port}: {e}")
                continue
    else:
        # Use specified ports
        if output_port:
            switch_output = initialize_switch(output_port, "Output Switch")
            if switch_output:
                used_ports.append(output_port)
        
        if input_port and input_port not in used_ports:
            switch_input = initialize_switch(input_port, "Input Switch")
            if switch_input:
                used_ports.append(input_port)
    
    # If we still don't have both switches, try additional ports
    if not switch_input or not switch_output:
        additional_ports = ["COM3", "COM4", "COM5", "COM6", "COM7", "/dev/ttyUSB0", "/dev/ttyUSB1"]
        
        for port in additional_ports:
            if port in used_ports:
                continue
                
            if not switch_output:
                switch_output = initialize_switch(port, "Output Switch")
                if switch_output:
                    used_ports.append(port)
                    continue
                    
            if not switch_input:
                switch_input = initialize_switch(port, "Input Switch")
                if switch_input:
                    used_ports.append(port)
    
    return switch_input, switch_output

def main():

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        logging.info("Set DPI awareness")
    except:
        pass
        logging.info("Failed to set DPI awareness")
    # Initialize the GUI theme
    AppData.load_calibration("calibration.json")

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # Load settings from JSON
    with open(SETTINGS_PATH, "r") as f:
        config = json.load(f)

    # List available Thorlabs devices
    available_devices = ThorlabsDevice.list_available_devices()
    logging.info(f"[Thorlabs] Found {len(available_devices)} Thorlabs devices:")
    for i, device in enumerate(available_devices):
        logging.info(f"{i+1}. {device['model']} (SN: {device['serial']})")
    
    # Initialize devices
    qontrol = QontrolDevice(config=config)
    # Connect to Qontrol device
    qontrol.connect()
    import_pickle(config)

    # Connect to multiple Thorlabs devices if available 
    thorlabs_devices = []
    
    if available_devices:
        # Connect to the first device
        thorlabs = ThorlabsDevice.get_device(
            serial=available_devices[0]['serial'], 
            config=config
        )
        thorlabs_devices.append(thorlabs)
        
        # Connect to additional devices if available
        if len(available_devices) > 1:
            thorlabs1 = ThorlabsDevice.get_device(
                serial=available_devices[1]['serial'], 
                config=config
            )
            thorlabs_devices.append(thorlabs1)
            
        if len(available_devices) > 2:
            thorlabs2 = ThorlabsDevice.get_device(
                serial=available_devices[2]['serial'], 
                config=config
            )
            thorlabs_devices.append(thorlabs2)
    else:
        # No devices found, use a mock device
        thorlabs = ThorlabsDevice(config=config)
        thorlabs.connect()
        thorlabs_devices.append(thorlabs)

    # daq = MockNIDAQ()
    # Attempt to use a DAQ device or mock if unavailable
    try:
        daq_devices_info = DAQ.list_available_devices()
        logging.info(f"[DAQ] Found {len(daq_devices_info)} NI-DAQ device(s):")
        for i, dev_info in enumerate(daq_devices_info):
            logging.info(f"{i+1}. {dev_info['product_type']} (Name: {dev_info['name']})")
    
        if len(daq_devices_info) == 0:
            logging.info("[DAQ] No DAQ devices found, using mock NI-DAQ device.")
            daq = MockDAQ()
        else:
            daq = DAQ.get_device(config=config)
    except DaqNotFoundError:
        logging.info("[DAQ] NI-DAQmx not found, using mock NI-DAQ device.")
        daq = MockDAQ()

    # Initialize switches
    switch_input, switch_output = initialize_dual_switches(config)

    # Print switch status
    logging.info("Switch Configuration:")
    logging.info(f"  Input Switch: {'Connected' if switch_input else 'Not connected'}")
    logging.info(f"  Output Switch: {'Connected' if switch_output else 'Not connected'}")

    # For backward compatibility - if only one switch is connected, use it as output
    if not switch_output and switch_input:
        logging.info("Only one switch detected, using it as output switch")
        switch_output = switch_input
        switch_input = None

    # Start the GUI application (you'll need to modify your MainWindow to handle multiple power meters)
    app = MainWindow(qontrol, thorlabs_devices, daq, switch_input, switch_output, config)
    app.mainloop()

    # Disconnect devices on exit
    for device in thorlabs_devices:
        device.disconnect()

    if daq is not None:
        daq.disconnect()

    qontrol.disconnect()

if __name__ == "__main__":
    main()
