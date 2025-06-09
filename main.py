# main.py
from app.imports import *
from app.utils.utils import import_pickle
import ctypes
from nidaqmx.errors import DaqNotFoundError 
from app.devices.switch_device import Switch
import serial.tools.list_ports

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "config", "settings.json")

def initialize_switch(port=None):
    """Initialize switch device with auto-detection or specified port"""
    if port:
        try:
            switch = Switch(port)
            # Test connection
            channel = switch.get_channel()
            if channel is not None:
                print(f"[INFO][Switch] Connected to {port}, current channel: {channel}")
                return switch
        except Exception as e:
            print(f"[ERROR][Switch] Failed to connect to {port}: {e}")
            return None
    else:
        # Auto-detect switch
        ports = serial.tools.list_ports.comports()
        for port_info in ports:
            try:
                switch = Switch(port_info.device)
                channel = switch.get_channel()
                if channel is not None:
                    print(f"[INFO][Switch] Auto-detected on {port_info.device}")
                    return switch
            except:
                continue
        print("[WARNING][Switch] No switch device detected")
        return None

def main():

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        print("[INFO] Set DPI awareness")
    except:
        pass
        print("[INFO] Failed to set DPI awareness")
    # Initialize the GUI theme

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # Load settings from JSON
    with open(SETTINGS_PATH, "r") as f:
        config = json.load(f)

    # List available Thorlabs devices
    available_devices = ThorlabsDevice.list_available_devices()
    print(f"[INFO][Thorlabs] Found {len(available_devices)} Thorlabs devices:")
    for i, device in enumerate(available_devices):
        print(f"{i+1}. {device['model']} (SN: {device['serial']})")
    
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
        print(f"[INFO][DAQ] Found {len(daq_devices_info)} NI-DAQ device(s):")
        for i, dev_info in enumerate(daq_devices_info):
            print(f"{i+1}. {dev_info['product_type']} (Name: {dev_info['name']})")
    
        if len(daq_devices_info) == 0:
            print("[INFO][DAQ] No DAQ devices found, using mock NI-DAQ device.")
            daq = MockDAQ()
        else:
            daq = DAQ.get_device(config=config)
    except DaqNotFoundError:
        print("[INFO][DAQ] NI-DAQmx not found, using mock NI-DAQ device.")
        daq = MockDAQ()

    # Initialize switch - try auto-detect first, then specific port
    switch = initialize_switch() or initialize_switch("COM5")

    # Start the GUI application (you'll need to modify your MainWindow to handle multiple power meters)
    app = MainWindow(qontrol, thorlabs_devices, daq, switch, config)
    app.mainloop()

    # Disconnect devices on exit
    for device in thorlabs_devices:
        device.disconnect()

    if daq is not None:
        daq.disconnect()

    qontrol.disconnect()

if __name__ == "__main__":
    main()
