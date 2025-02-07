# MZIC project structure

MZIC/
├── main.py                     # Main entry point for the application.
├── README.md                   # Project documentation.
├── requirements.txt            # Python dependencies.
├── .git/                      # Git repository files.
│   └── .gitignore            # Files/folders to ignore in version control.
├── .vscode/                   # VSCode workspace settings.
│   └── settings.json         # Workspace-specific settings for VSCode.
├── app/                       # Main application code.
│   ├── imports.py              # Common module imports.
│   ├── __init__.py             # Initializes the app package.
│   ├── devices/                # Modules for interfacing with hardware devices.
│   │   ├── mock_devices.py     # Mock implementations for testing.
│   │   ├── qontrol_device.py   # Interface for the Qontrol device.
│   │   ├── thorlabs_device.py  # Interface for the Thorlabs device.
│   │   └── __init__.py         # Initializes the devices subpackage.
│   ├── gui/                    # Graphical User Interface (GUI) components.
│   │   ├── main_window.py      # Main window of the application.
│   │   ├── widgets.py          # Custom widgets for the GUI.
│   │   ├── window1.py          # Layout for "Window 1".
│   │   ├── window2.py          # Layout for "Window 2" (if implemented).
│   │   └── __init__.py         # Initializes the gui subpackage.
│   ├── mqtt/                   # Modules for MQTT communication.
│   │   ├── client.py           # Base MQTT client implementation.
│   │   ├── desktop_subscriber.py  # MQTT subscriber for desktop usage.
│   │   └── pi_publisher.py     # MQTT publisher for Raspberry Pi.
│   ├── utils/                  # Utility functions and helper modules.
│   │   ├── appdata.py          # Application data and configuration parameters.
│   │   ├── exportfunc.py       # Functions to export data (e.g., to pickle or CSV).
│   │   ├── grid.py             # Functions to build and manage the grid view.
│   │   ├── importfunc.py       # Functions to import data (e.g., from a pickle file).
│   │   ├── lines.py            # Functions for processing line elements.
│   │   └── utils.py            # Miscellaneous utility functions.
│   └── __pycache__/            # Compiled Python files (ignored in version control).
├── config/                   # Application configuration files.
│   └── settings.json         # Application settings.
├── docs/                     # Project documentation and manuals.
└── tests/                    # Automated tests for the project.
