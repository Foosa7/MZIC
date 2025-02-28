# app/utils/qset.py
import json
import argparse
from app.devices.qontrol_device import QontrolDevice
from app.utils.qontrol.qmapper8x8 import create_label_mapping, clamp_value

class QontrolSetter:
    def __init__(self, config_path, grid_size="8x8", verbose=False):
        self.config_path = config_path
        self.grid_size = grid_size
        self.verbose = verbose
        self.q_device = QontrolDevice()
        self.label_map = None

    def connect_device(self):
        if not self.q_device.connect():
            raise ConnectionError("Failed to connect to Qontrol device")
        if self.verbose:
            print(f"Connected to Qontrol with {self.q_device.params['Available channels']} channels")

    def load_config(self):
        with open(self.config_path) as f:
            config = json.load(f)
        
        n = int(self.grid_size.split('x')[0])
        self.label_map = create_label_mapping(n)
        
        self.current_config = {}
        for label, settings in config.items():
            if label in self.label_map:
                theta_ch, phi_ch = self.label_map[label]
                self.current_config[label] = {
                    'theta': clamp_value(settings.get('theta', 0), self.q_device.globalcurrrentlimit),
                    'phi': clamp_value(settings.get('phi', 0), self.q_device.globalcurrrentlimit),
                    'theta_ch': theta_ch,
                    'phi_ch': phi_ch
                }
        if self.verbose:
            print(f"Loaded configuration for {len(self.current_config)} elements")

    def apply_configuration(self):
        if not self.label_map:
            raise ValueError("Configuration not loaded")
        
        for label, settings in self.current_config.items():
            try:
                self.q_device.set_current(settings['theta_ch'], settings['theta'])
                self.q_device.set_current(settings['phi_ch'], settings['phi'])
                if self.verbose:
                    print(f"Set {label}: θ{settings['theta_ch']}={settings['theta']}mA, φ{settings['phi_ch']}={settings['phi']}mA")
            except Exception as e:
                print(f"Error setting {label}: {str(e)}")

    def run(self):
        try:
            self.connect_device()
            self.load_config()
            self.apply_configuration()
            if self.verbose:
                self.q_device.show_status()
        except Exception as e:
            print(f"Configuration failed: {str(e)}")
        finally:
            self.q_device.disconnect()

def main():
    parser = argparse.ArgumentParser(description="Qontrol Current Configuration Tool")
    parser.add_argument("config_file", help="Path to JSON configuration file")
    parser.add_argument("-g", "--grid", default="8x8", help="Grid size (e.g., 4x4, 6x6, 8x8)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    setter = QontrolSetter(
        config_path=args.config_file,
        grid_size=args.grid,
        verbose=args.verbose
    )
    setter.run()

if __name__ == "__main__":
    main()
