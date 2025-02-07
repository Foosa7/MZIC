# app/utils/importfunc.py

import os
import pickle
from io import BytesIO
from tkinter import filedialog, messagebox

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

    messagebox.showinfo("Import Complete",
                        f"{import_file}")
