# app/utils/utils.py

import math
import numpy as np
import sympy as sp
from tkinter import messagebox
import os
import pickle
from io import BytesIO
from tkinter import filedialog, messagebox
import json

def load_config(config_path="config/settings.json"):
    """Load the configuration file."""
    if os.path.exists(config_path):
        with open(config_path, "r") as file:
            return json.load(file)
    return {}

def import_pickle(config):
    """Loads a pickle file from the path in config and returns the data."""
    import_file = config.get("default_config", "")

    # Ensure the file path is correctly formatted for Windows
    import_file = os.path.normpath(import_file)

    if not import_file or not os.path.exists(import_file):
        print(f"[ERROR] Default pickle file not found: {import_file}")
        return None

    with open(import_file, "rb") as file:
        imported_data = pickle.load(file)

    print(f"[INFO] Successfully imported {import_file}")
    return imported_data  # Return the loaded data

def importfunc(obj):
    """
    Opens a file dialog to select a pickle file, then imports data from it
    and updates the attributes of the given object 'obj'.
    
    Expected keys in the imported dictionary:
      - 'caliparamlist_lin_cross'
      - 'caliparamlist_lin_bar'
      - 'caliparamlist_lincub_cross'
      - 'caliparamlist_lincub_bar'
      - 'standard_matrices'
      - 'image_map'
      
    The function also reassigns the 'fitfunc' in the matrices if its value is 'fit_cos_func'
    by setting it to obj.fit_cos.
    """
    
    # Ask for the import file.
    import_file = filedialog.askopenfilename(
        title="Open Import File",
        filetypes=[("Pickle Files", "*.pkl")]
    )
    if not import_file:
        messagebox.showinfo("Import Canceled", "No file selected for import.")
        return

    # Load the imported data from the pickle file.
    with open(import_file, "rb") as file:
        imported = pickle.load(file)

    # Reassign the fitfunc back from the reference string.
    for key in ['caliparamlist_lin_cross', 'caliparamlist_lin_bar',
                'caliparamlist_lincub_cross', 'caliparamlist_lincub_bar']:
        if hasattr(obj, key):
            matrix = getattr(obj, key)
            for i, data in enumerate(matrix):
                if isinstance(data, dict) and 'fitfunc' in data:
                    if data['fitfunc'] == 'fit_cos_func':
                        data['fitfunc'] = obj.fit_cos  # Replace with the actual function reference.
                    matrix[i] = data  # Replace with the modified data.

    # Import standard matrices.
    standard_matrices = imported.get("standard_matrices", {})
    for attr_name, matrix in standard_matrices.items():
        if hasattr(obj, attr_name):
            setattr(obj, attr_name, matrix)

    # Import BytesIO matrices from images.
    import_dir = os.path.dirname(import_file)
    image_map = imported.get("image_map", {})
    for matrix_name, image_filenames in image_map.items():
        if hasattr(obj, matrix_name):
            matrix = getattr(obj, matrix_name)
            if isinstance(matrix, list):
                for i, filename in enumerate(image_filenames):
                    image_path = os.path.join(import_dir, filename)
                    if os.path.exists(image_path):
                        with open(image_path, "rb") as img_file:
                            buf = BytesIO(img_file.read())
                            buf.seek(0)  # Reset position
                            # Extend the list if necessary.
                            if i >= len(matrix):
                                matrix.extend([None] * (i + 1 - len(matrix)))
                            matrix[i] = buf

def create_zero_config(grid_size):
    """Create a configuration with all theta and phi values set to zero"""
    n = int(grid_size.split('x')[0])
    zero_config = {}
    
    for row in range(n):
        row_letter = chr(65 + row)
        for col in range(1, n+1):
            cross_label = f"{row_letter}{col}"
            zero_config[cross_label] = {
                "arms": ["TL", "TR", "BL", "BR"],
                "theta": "0",
                "phi": "0"
            }
    
    return json.dumps(zero_config)

def calculate_current_for_phase(channel, phase_value, app_data, *io_configs):
    """Calculate current for a given phase value"""
    for io_config in io_configs:
        if io_config == "cross" and channel < len(app_data.caliparamlist_lincub_cross) and app_data.caliparamlist_lincub_cross[channel] != "Null":
            params = app_data.caliparamlist_lincub_cross[channel]
            return calculate_current_from_params(channel, phase_value, params, app_data)
        elif io_config == "bar" and channel < len(app_data.caliparamlist_lincub_bar) and app_data.caliparamlist_lincub_bar[channel] != "Null":
            params = app_data.caliparamlist_lincub_bar[channel]
            return calculate_current_from_params(channel, phase_value, params, app_data)
    return None


