# main.py
from app.imports import *
import ctypes
from nidaqmx.errors import DaqNotFoundError 

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "config", "settings.json")

def main():

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        print("Set DPI awareness")
    except:
        pass
        print("Failed to set DPI awareness")
    # Initialize the GUI theme

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # Load settings from JSON
    with open(SETTINGS_PATH, "r") as f:
        config = json.load(f)

    # List available Thorlabs devices
    available_devices = ThorlabsDevice.list_available_devices()
    print(f"Found {len(available_devices)} Thorlabs devices:")
    for i, device in enumerate(available_devices):
        print(f"{i+1}. {device['model']} (SN: {device['serial']})")
    
    # Initialize devices
    qontrol = QontrolDevice(config=config)
    
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

    # Attempt to use a DAQ device or mock if unavailable
    try:
        daq_devices_info = DAQ.list_available_devices()
        if len(daq_devices_info) == 0:
            print("No DAQ devices found, using mock NI-DAQ device.")
            daq = MockNIDAQ()
        else:
            daq = DAQ.get_device(config=config)
            if daq:
                daq.connect()
            else:
                print("DAQ.get_device() returned None; using mock DAQ.")
                daq = MockNIDAQ()
    except DaqNotFoundError:
        print("NI-DAQmx package not found or not installed. Using mock DAQ.")
        daq = MockNIDAQ()

        print(f"Found {len(daq_devices_info)} NI-DAQ device(s):")
        for i, dev_info in enumerate(daq_devices_info):
            print(f"{i+1}. {dev_info['product_type']} (Name: {dev_info['name']})")
    
        if len(daq_devices_info) == 0:
            print("No DAQ devices found, using mock NI-DAQ device.")
            daq = MockNIDAQ()
        else:
            daq = DAQ.get_device(config=config)
    except DaqNotFoundError:
        print("NI-DAQmx not found, using mock NI-DAQ device.")
        daq = MockNIDAQ()


    # Connect to Qontrol device
    qontrol.connect()

    # Start the GUI application (you'll need to modify your MainWindow to handle multiple power meters)
    app = MainWindow(qontrol, thorlabs_devices, daq, config)
    app.mainloop()

    # Disconnect devices on exit
    for device in thorlabs_devices:
        device.disconnect()

    if daq is not None:
        daq.disconnect()

    qontrol.disconnect()

if __name__ == "__main__":
    main()
