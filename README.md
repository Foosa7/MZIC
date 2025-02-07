# MZIC project structure

MZIC/
│   main.py                     # Main entry point for the application.
│   README.md                   # Project documentation (this file).
│   requirements.txt            # List of Python dependencies.
│
├───.git                        # Git repository files.
│       .gitignore              # Files/folders to ignore in version control.
│
├───.vscode                     # VSCode settings.
│       settings.json           # Workspace-specific settings for VSCode.
│
├───app                         # Main application code.
│   │   imports.py              # Common imports used throughout the application.
│   │   __init__.py             # Initializes the app package.
│   │
│   ├───devices                # Modules interfacing with hardware devices.
│   │       mock_devices.py     # Mock implementations of devices for testing.
│   │       qontrol_device.py     # Interface for the Qontrol device.
│   │       thorlabs_device.py    # Interface for the Thorlabs device.
│   │       __init__.py         # Initializes the devices subpackage.
│   │
│   ├───gui                    # Graphical User Interface (GUI) components.
│   │       main_window.py      # Main window of the application.
│   │       widgets.py          # Custom widgets used across the GUI.
│   │       window1.py          # Content and layout for "Window 1".
│   │       window2.py          # Content for "Window 2" (if implemented).
│   │       __init__.py         # Initializes the gui subpackage.
│   │
│   ├───mqtt                   # Modules for MQTT communication.
│   │       client.py           # Base MQTT client implementation.
│   │       desktop_subscriber.py  # MQTT subscriber for desktop usage.
│   │       pi_publisher.py     # MQTT publisher for Raspberry Pi (or similar).
│   │
│   ├───utils                  # Utility functions and helper modules.
│   │       appdata.py          # Defines the AppData class with configuration matrices and parameters.
│   │       exportfunc.py       # Functions to export data (e.g. to pickle or CSV).
│   │       grid.py             # Functions to build and manage the grid view.
│   │       importfunc.py       # Functions to import data (e.g. from a pickle file).
│   │       lines.py            # Functions for processing line elements.
│   │       utils.py            # Miscellaneous utility functions (e.g. apply_phase).
│   │
│   └───__pycache__            # Compiled Python files (ignored in version control).
│
├───config                     # Configuration files for the application.
│       settings.json           # Application settings.
│
├───docs                       # Project documentation and manuals.
│
└───tests                      # Automated tests for the project.

