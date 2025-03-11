# main.py
from app.imports import *

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "config", "settings.json")

def main():
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

    # Connect to Qontrol device
    qontrol.connect()

    # Start the GUI application (you'll need to modify your MainWindow to handle multiple power meters)
    app = MainWindow(qontrol, thorlabs_devices, config)
    app.mainloop()

    # Disconnect devices on exit
    qontrol.disconnect()
    for device in thorlabs_devices:
        device.disconnect()

if __name__ == "__main__":
    main()
