# MZIC - Mach-Zehnder Interferometer Controller

GUI-based control system for programmable photonic circuits, providing automated calibration, unitary matrix implementation, and real-time monitoring of Mach-Zehnder interferometer (MZI) mesh networks. This software enables researchers to configure and operate reconfigurable photonic processors for applications in quantum computing, machine learning, and optical signal processing. Features include interactive grid-based phase control, automated resistance and phase characterization, parameter sweep functionality, and comprehensive data logging. The platform seamlessly integrates with Qontrol multi-channel current sources for thermal phase shifting, Thorlabs optical power meters, National Instruments DAQ systems for multi-channel measurements, and programmable optical switches for automated routing and characterization.

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/Foosa7/MZIC)

## Quick Start

```bash
# Install
git clone https://github.com/Foosa7/MZIC.git
cd MZIC
conda create -n mzic python=3.8
conda activate mzic
pip install -r requirements.txt

# Run
python main.py
```

![Application Architecture](https://github.com/Foosa7/MZIC/blob/auto_calibrate/docs/assets/APP_ARCH.drawio.png)


## Features

- **Multi-device Control**: Qontrol (64ch), Thorlabs power meters, NI USB-6000 DAQ, 1×12 optical switch
- **Interactive Grid UI**: Click-and-drag MZI path selection with real-time phase control
- **Automated Calibration**: Resistance (cubic+linear fit) and phase (cosine fit) characterization
- **Advanced Operations**: Parameter sweeps, unitary decomposition, phase interpolation
- **Remote Control**: MQTT interface for distributed experiments

## Main Interface

### Mesh Tab
- **Grid**: Select MZI paths and set θ/φ values
- **Buttons**: Import/Export | Current | Clear | R | P | Phase
- **Panels**: Interpolation | Mapping | Monitor | Graphs | Status | Sweep | Switch

### Calibrate Tab
- Individual channel control with real-time monitoring
- Calibration data visualization

### Unitary Tab
- Matrix decomposition (Clements/Reck algorithms)
- Automated unitary cycling experiments

## Key Operations

### Basic Usage
1. Select MZI crosspoint (e.g., A1)
2. Enter theta/phi values
3. Click "Phase" to apply

### Calibration
```python
# Resistance: Select crosspoint → Choose θ/φ → Click "R"
# Phase: Connect Thorlabs → Select crosspoint → Click "P"
```

### Sweep Example
```
Target: A1
Parameter: theta
Range: 0π to 2π
Steps: 20
Dwell: 1000ms
```

### Configuration Format
```json
{
    "A1": {"arms": ["TL", "BR"], "theta": "1.57", "phi": "0.785"},
    "B2": {"arms": ["TR", "BL"], "theta": "0", "phi": "3.14"}
}
```

## Hardware Setup

| Device | Connection | Notes |
|--------|------------|-------|
| Qontrol | USB/FTDI | 64 channels, 20mA limit |
| Thorlabs | USB | Multiple devices supported |
| NI DAQ | USB | Channels ai0-ai7, 1kHz default |
| Switch | Serial COM | 115200 baud, 1×12 config |

## Advanced Features

### Unitary Decomposition
```python
U = np.load('unitary.npy')
I = unitary.decomposition(U, global_phase=True)
json_output = mzi_lut.get_json_output(n, I.BS_list, input_pin, output_pin)
```

### Path Sequencing
```bash
# Paste JSON sequence → Set delay → Run
[{"A1": {"theta": "0", "phi": "0"}}, {"A1": {"theta": "1.57", "phi": "0"}}]
```

### Phase Interpolation
The method is based on the heatingpower--opticalpower curve would change along time but not so far away from the initial cablibration file. A quick and realistic idea shall be sweep the certain nodes, and do the interpolation to get the slightly changed new phase.
- Load sweep CSV files
- Enable interpolation
- Automatic phase correction

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Device not detected | Check USB/drivers |
| Switch error | Verify COM port, 115200 baud |
| Calibration fails | Check optical power levels |
| Phase < offset | System auto-adds 2π |

## Project Structure

```
MZIC/
├── .vscode/                        # VSCode workspace settings
│   └── settings.json               # VSCode configuration
├── app/                            # Main application code
│   ├── devices/                    # Hardware device interfaces
│   │   ├── __init__.py             # Package initializer
│   │   ├── daq_device.py           # NI DAQ interface
│   │   ├── mock_devices.py         # Mock device implementations for testing
│   │   ├── qontrol_device.py       # Qontrol phase shifter interface
│   │   ├── switch_device.py        # Optical switch interface
│   │   └── thorlabs_device.py      # Thorlabs power meter interface
│   ├── gui/                        # Graphical User Interface components
│   │   ├── __init__.py             # Package initializer
│   │   ├── main_window.py          # Main application window
│   │   ├── widgets.py              # Custom GUI widgets
│   │   ├── window1.py              # Mesh control interface
│   │   ├── window2.py              # Calibration interface
│   │   └── window3.py              # Unitary transformation interface
│   ├── mqtt/                       # MQTT communication modules
│   │   └── control_app.py          # MQTT control application
│   ├── utils/                      # Utility functions and helpers
│   │   ├── calibrate/              # Calibration utilities
│   │   ├── gui/                    # GUI utility functions
│   │   ├── interpolation/          # Phase interpolation system
│   │   │   ├── data/               # Interpolation data files
│   │   │   │   ├── E1_theta_200_steps.csv    # E1 theta sweep data
│   │   │   │   ├── E2_theta_200_steps.csv    # E2 theta sweep data
│   │   │   │   ├── F1_theta_200_steps.csv    # F1 theta sweep data
│   │   │   │   ├── G1_theta_200_steps.csv    # G1 theta sweep data
│   │   │   │   ├── G2_theta_200_steps.csv    # G2 theta sweep data
│   │   │   │   └── H1_theta_200_steps.csv    # H1 theta sweep data
│   │   │   ├── __init__.py                 # Package initializer
│   │   │   └── Reader_interpolation.py    # Interpolation reader/processor
│   │   ├── qontrol/                # Qontrol-specific utilities
│   │   │   ├── qmapper8x8.py       # Clements mesh to chip pin mapping
│   │   │   └── qset.py             # Current value setter for Qontrol
│   │   ├── unitary/                # Unitary transformation modules
│   │   │   ├── mzi_convention.py   # BS angle convention conversion
│   │   │   ├── mzi_lut.py          # MZI lookup tables
│   │   │   └── unitary.py          # Unitary decomposition
│   │   ├── appdata.py              # Application data management
│   │   ├── config_manager.py       # Configuration file manager
│   │   ├── grid.py                 # Grid view management
│   │   ├── map.json                # Channel mapping configuration
│   │   ├── switch_measurements.py  # Switch measurement utilities
│   │   └── utils.py                # General utility functions
│   ├── __init__.py                 # Package initializer
│   └── imports.py                  # Common module imports
├── config/                         # Configuration and calibration files
│   ├── 8_modechip_20241212_25deg_3mWinput_1550nm/    # Calibration dataset
│   │   └── 8_modechip_20241212_25deg_3mWinput_1550nm.pkl
│   ├── 8_modechip_20250116_25deg_25mWinput_1550nm.pkl    # Calibration data
│   ├── 8_modechip_20250514_25deg_1550.pkl                # Calibration data
│   ├── export.json                 # Exported configuration
│   ├── newcal.pkl                  # Calibration data
│   └── settings.json               # Application settings
├── docs/                           # Documentation
│   └── README.md                   # Documentation readme
├── tests/                          # Test suite
│   ├── interpolation/              # Interpolation tests
│   │   └── data/                   # Test data for interpolation
│   ├── daq-calibration.py          # DAQ calibration test
│   ├── daq-test.py                 # DAQ functionality test
│   ├── labelmap.py                 # Label mapping test
│   ├── qontrol-log.py              # Qontrol logging test
│   ├── qontrol_test.py             # Qontrol functionality test
│   ├── switch-test.py              # Optical switch test utility
│   └── thorlabs-test.py            # Thorlabs device test
├── .gitignore                      # Git ignore patterns
├── main.py                         # Main entry point for the application
├── README.md                       # Project documentation
└── requirements.txt                # Python dependencies
```

## Development

```bash
# Test devices
python tests/switch-test.py
python tests/qontrol_test.py
```

## API Reference

```python
# Core classes
QontrolDevice.set_current(channel, current)
Switch.set_channel(channel)
Window1Content.apply_phase_new()
Window3Content.cycle_unitaries()
```

## Requirements


### Software
- Python 3.8+ (see requirements.txt for a list of modules)
- Operating System:
  - **Windows**: Fully supported (all devices tested)
  - **Linux**: Partial support (Thorlabs tested; DAQ requires proper NI-DAQmx driver installation)
  - **macOS**: Untested

### Hardware Drivers
- **Windows**: 
  - NI-DAQmx drivers (for DAQ functionality)
  - FTDI drivers (for Qontrol device)
  - Thorlabs power meter (PM100D) drivers 
- **Linux**:
  - Thorlabs drivers (confirmed working)
  - NI-DAQmx drivers (requires manual installation from NI)
  - FTDI drivers (confirmed working, typically included in kernel)

## Acknowledgments
- Clements et al. for the optimal interferometer design algorithm
- The unitary decomposition (`unitary.py`) is based on the [interferometer package](https://github.com/clementsw/interferometer) by William Clements
