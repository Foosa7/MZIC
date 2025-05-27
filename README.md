# MZIC project structure

Always a good idea to create a new environment with [Anaconda](https://www.anaconda.com/download/success) 

### Step 1
```
git clone https://github.com/Foosa7/MZIC.git
```
### Step 2
```
cd /project directory
```

### Step 3 
```
pip install -r /path/to/requirements.txt
```

### Step 4
```
python main.py
```

```
MZIC/
├── .git/                           # Git repository files.
│   └── .gitignore                  # Files/folders to ignore in version control.
├── .vscode/                        # VSCode workspace settings.
│   └── settings.json               # Workspace-specific settings for VSCode.
├── README.md                       # Project documentation.
├── config/                         # Application configuration files.
│   └── settings.json               # Application settings.
├── docs/                           # Project documentation and manuals.
├── main.py                         # Main entry point for the application.
├── requirements.txt                # Python dependencies.
├── app/                            # Main application code.
│   ├── __init__.py                 # Initializes the app package.
│   ├── imports.py                  # Common module imports.
│   ├── devices/                    # Modules for interfacing with hardware devices.
│   │   ├── __init__.py             # Initializes the devices subpackage.
│   │   ├── daq_device.py           # Interface for the DAQ device.
│   │   ├── mock_devices.py         # Mock implementations for testing.
│   │   ├── qontrol_device.py       # Interface for the Qontrol device.
│   │   ├── switch_device.py        # Interface for the optical switch device.
│   │   └── thorlabs_device.py      # Interface for the Thorlabs device.
│   ├── gui/                        # Graphical User Interface (GUI) components.
│   │   ├── __init__.py             # Initializes the gui subpackage.
│   │   ├── main_window.py          # Main window of the application.
│   │   ├── widgets.py              # Custom widgets for the GUI.
│   │   ├── window1.py              # Layout for "Window 1".
│   │   ├── window2.py              # Layout for "Window 2".
│   │   └── window3.py              # Layout for "Window 3".
│   ├── mqtt/                       # Modules for MQTT communication.
│   │   ├── client.py               # Base MQTT client implementation.
│   │   ├── desktop_subscriber.py   # MQTT subscriber for desktop usage.
│   │   └── pi_publisher.py         # MQTT publisher for Raspberry Pi.
│   ├── utils/                      # Utility functions and helper modules.
│   │   ├── appdata.py              # Application data and configuration parameters.
│   │   ├── exportfunc.py           # Functions to export data (e.g., to pickle or CSV).
│   │   ├── grid.py                 # Functions to build and manage the grid view.
│   │   ├── importfunc.py           # Functions to import data (e.g., from a pickle file).
│   │   ├── qontrol/                # Qontrol-specific helpers.
│   │   │   ├── __init__.py         # Initializes the qontrol subpackage.
│   │   │   ├── qmapper8x8.py       # Maps from the Clements mesh layout to the chip pin number.
│   │   │   └── qset.py             # Sets current values to the qontrol module from qmapper.
│   │   ├── unitary/                # Modules for unitary transformations and MZI mappings.
│   │   │   ├── mzi_convention.py   # Converts the BS angles from Clements convention to chip convention.
│   │   │   ├── mzi_lut.py          # Lookup table for mapping angles to MZIs.
│   │   │   └── unitary.py          # Interferometer package for unitary decomposition.
│   │   └── utils.py                # Miscellaneous utility functions.
│   └── __pycache__/                # Compiled Python files (ignored in version control).
└── tests/                          # Automated tests for the project.
```
