# app/imports.py

# Set matplotlib backend first
import matplotlib
matplotlib.use('TkAgg')  # Set backend before other matplotlib imports

# Standard Library Imports
import os
import sys
import time
import json
import pickle
import random
import string
import shutil
import traceback
import ast
import ctypes
from datetime import datetime
from scipy.linalg import expm
import argparse
from pathlib import Path


# Third-Party Libraries
import serial
import serial.tools.list_ports
import pyvisa
import numpy as np

# Matplotlib imports
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, 
    NavigationToolbar2Tk
)
import matplotlib.ticker as ticker
from matplotlib.ticker import FuncFormatter

# Other third-party
from unittest.mock import MagicMock
from PIL import Image, ImageTk
import sympy as sp
import interferometer as itf
import pnn
from pnn.methods import decompose_clements, reconstruct_clements

# CustomTkinter GUI
import customtkinter as ctk
from tkinter import Tk, Label, filedialog, messagebox, ttk

# Hardware Interfaces
import qontrol
from ThorlabsPM100 import ThorlabsPM100
import nidaqmx
from nidaqmx.system import System

# Import Custom Modules
from app.devices.daq_device import DAQ
from app.devices.qontrol_device import QontrolDevice
from app.devices.thorlabs_device import ThorlabsDevice
from app.devices.mock_devices import MockQontrol, MockThorlabsPM100, MockDAQ
from app.gui.main_window import MainWindow  
from app.utils.appdata import AppData

