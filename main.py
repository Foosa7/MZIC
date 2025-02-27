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

    # Initialize devices (replace with Mock devices for testing)
    qontrol = QontrolDevice(config=config)  # Replace with QontrolDevice for real hardware
    # qontrol = MockQontrol() # Replace with QontrolDevice for real hardware
    thorlabs = MockThorlabsPM100()  # Replace with ThorlabsDevice for real hardware

    # Connect to devices
    qontrol.connect()
    thorlabs.connect()

    # Start the GUI application
    app = MainWindow(qontrol, thorlabs, config)
    app.mainloop()

    # Disconnect devices on exit
    qontrol.disconnect()
    thorlabs.disconnect()

if __name__ == "__main__":
    main()


