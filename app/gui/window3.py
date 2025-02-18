# app/gui/window3.py
from app.imports import *
import customtkinter as ctk
import tkinter.simpledialog as simpledialog
import tkinter.filedialog as filedialog
import numpy as np
from qoptcraft.operators import haar_random_unitary
from app.utils import grid  
from app.utils import angle_mapper
from app.utils import clemens

class Window3Content(ctk.CTkFrame):
    
    def __init__(self, master, channel, fit, IOconfig, app, qontrol, grid_size="8x8", **kwargs):
        super().__init__(master, **kwargs)
        self.channel = channel
        self.fit = fit
        self.IOconfig = IOconfig
        self.app = app
        self.qontrol = qontrol
        self.grid_size = grid_size
        
        # -- Main content layout --
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Left: photonic mesh diagram
        self.grid_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.grid_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Right: controls
        self.right_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        self.build_grid(self.grid_size)
        
        # -- Import/Export path buttons at top --
        self.import_export_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.import_export_frame.pack(fill="x", padx=5, pady=(5,2))
        
        self.export_button = ctk.CTkButton(
            self.import_export_frame,
            text="Export",
            command=self.export_paths,
            height=20, width=60
        )
        self.export_button.pack(side="left", padx=1)
        
        self.import_button = ctk.CTkButton(
            self.import_export_frame,
            text="Import",
            command=self.import_paths,
            height=20, width=60
        )
        self.import_button.pack(side="left", padx=1)
        
        # -- Text box for path info --
        self.selected_paths_display = ctk.CTkTextbox(self.right_frame, width=200, height=80)
        self.selected_paths_display.pack(fill="x", padx=5, pady=(2,5))
        
        # -- Print MZI values button --
        self.print_button = ctk.CTkButton(
            self.right_frame, text="Print Values",
            command=self.print_input_values,
            height=20, width=60
        )
        self.print_button.pack(fill="x", padx=5, pady=(2,5))

        # =====================================
        #  Centered unitary panel
        # =====================================
        # A container to center the unitary
        self.unitary_container = ctk.CTkFrame(self.right_frame, fg_color="gray25")
        self.unitary_container.pack(fill="both", expand=True, padx=5, pady=(10,5))
        
        # We'll nest the actual grid of entries in a sub‐frame.
        # Pack or grid it with anchor='center' to center it.
        self.unitary_entries_frame = ctk.CTkFrame(self.unitary_container, fg_color="gray20")
        self.unitary_entries_frame.pack(anchor="center", pady=10)

        # Determine dimension n from mesh size
        self.n = int(self.grid_size.split('x')[0])
        self.unitary_entries = []
        for i in range(self.n):
            row_entries = []
            for j in range(self.n):
                e = ctk.CTkEntry(self.unitary_entries_frame, width=40)
                e.grid(row=i, column=j, padx=2, pady=2)
                row_entries.append(e)
            self.unitary_entries.append(row_entries)

        # -- “Apply Unitary” / file import / file export / common unitaries --
        self.bottom_buttons_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.bottom_buttons_frame.pack(fill="x", padx=5, pady=5)

        # Apply the NxN data
        self.apply_unitary_button = ctk.CTkButton(
            self.bottom_buttons_frame, text="Apply Unitary",
            command=self.apply_unitary_and_decompose
        )
        self.apply_unitary_button.pack(fill="x", pady=(5,5))

        # 1) Button to import from file
        self.import_unitary_button = ctk.CTkButton(
            self.bottom_buttons_frame, text="Import Unitary",
            command=self.import_unitary_file
        )
        self.import_unitary_button.pack(fill="x", pady=(5,5))

        # 2) Button to export to file
        self.export_unitary_button = ctk.CTkButton(
            self.bottom_buttons_frame, text="Export Unitary",
            command=self.export_unitary_file
        )
        self.export_unitary_button.pack(fill="x", pady=(5,5))

        # 3) Common unitaries frame
        self.common_unitaries_frame = ctk.CTkFrame(self.bottom_buttons_frame, fg_color="transparent")
        self.common_unitaries_frame.pack(fill="x", pady=(5,5))

        # Identity
        self.identity_button = ctk.CTkButton(
            self.common_unitaries_frame, text="Identity",
            command=self.fill_identity
        )
        self.identity_button.pack(side="left", expand=True, fill="x", padx=2)

        # Haar random
        self.haar_button = ctk.CTkButton(
            self.common_unitaries_frame, text="Haar Random",
            command=self.fill_haar_random
        )
        self.haar_button.pack(side="left", expand=True, fill="x", padx=2)

        # Let the left side (mesh) get more space
        self.content_frame.grid_columnconfigure(0, weight=9)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

    # -----------------------------------
    # Mesh building / updating
    # -----------------------------------
    def build_grid(self, grid_size):
        try:
            n = int(grid_size.split('x')[0])
        except:
            n = 8
        scale = 0.8 if n == 12 else 1.0
        self.custom_grid = grid.Example(self.grid_container, grid_n=n, scale=scale)
        self.custom_grid.pack(expand=True, fill="both")
        self.custom_grid.selection_callback = self.update_selected_paths

    def update_selected_paths(self, selected_str):
        self.selected_paths_display.delete("0.0", "end")
        self.selected_paths_display.insert("0.0", selected_str)

    # -----------------------------------
    # Import/Export path (the “paths” JSON)
    # -----------------------------------
    def export_paths(self):
        json_str = self.custom_grid.export_paths_json()
        self.selected_paths_display.delete("0.0", "end")
        self.selected_paths_display.insert("0.0", json_str)

    def import_paths(self):
        json_str = simpledialog.askstring("Import Paths", "Enter JSON for selected paths:")
        print('test')
        if json_str:
            self.custom_grid.import_paths_json(json_str)
            self.custom_grid.update_selection()

    def update_grid(self, new_grid_size):
        cover = ctk.CTkFrame(self.grid_container, fg_color="grey16", border_width=0)
        cover.place(relwidth=1, relheight=1)
        self.grid_container.update_idletasks()
        for widget in self.grid_container.winfo_children():
            widget.destroy()
        self.build_grid(new_grid_size)
        cover.destroy()

    # -----------------------------------
    # Print MZI (theta, phi) values
    # -----------------------------------
    def print_input_values(self):
        if not hasattr(self.custom_grid, 'input_boxes'):
            print("No input boxes found.")
            return
        for cross_label, widget_dict in self.custom_grid.input_boxes.items():
            theta_value = widget_dict['theta_entry'].get()
            phi_value = widget_dict['phi_entry'].get()
            print(f"Cross {cross_label}: theta = {theta_value}, phi = {phi_value}")

    # -----------------------------------
    # 1) “Apply Unitary” – read NxN from entries, decompose
    # -----------------------------------
    def apply_unitary_and_decompose(self):
        U = self.read_unitary_entries()
        if U is None:
            return
        try:
            left_list, diag, right_list, left_angles, right_angles = clemens.clemens_decomposition(U)
            print("Clements decomposition done.")
            
            all_angles = left_angles + right_angles # (Temp) Add all angles together - just for testing angle_ mapper function
            json_str = angle_mapper.build_angle_json(all_angles, self.n)
            self.custom_grid.import_paths_json(json_str)
            self.custom_grid.update_selection()
            
        except Exception as e:
            print("Error in decomposition:", e)

    # -----------------------------------
    # 2) Import unitary from file
    # -----------------------------------
    def import_unitary_file(self):
        """Ask the user for a file, parse it as NxN, and fill the unitary entries."""
        path = filedialog.askopenfilename(
            title="Select Unitary File",
            filetypes=[("CSV files","*.csv"), ("NumPy files","*.npy"), ("All files","*.*")]
        )
        if not path:
            return
        
        # Basic example: if CSV, use np.loadtxt. If .npy, use np.load.  
        # You could handle automatically or check file extension.
        try:
            if path.endswith(".npy"):
                U = np.load(path)
            else:
                # Assume CSV or text
                U = np.loadtxt(path, dtype=complex, delimiter=",")
            self.fill_unitary_entries(U)
        except Exception as e:
            print("Failed to import unitary file:", e)

    # -----------------------------------
    # 3) Export Unitary to file
    # -----------------------------------
    def export_unitary_file(self):
        """Read the NxN from entries and save to file (CSV or .npy)."""
        U = self.read_unitary_entries()
        if U is None:
            return
        
        path = filedialog.asksaveasfilename(
            title="Save Unitary File",
            defaultextension=".csv",
            filetypes=[("CSV files","*.csv"), ("NumPy files","*.npy"), ("All files","*.*")]
        )
        if not path:
            return
        
        try:
            if path.endswith(".npy"):
                np.save(path, U)
            else:
                # default to CSV
                np.savetxt(path, U, delimiter=",", fmt="%s")
            print("Unitary saved successfully.")
        except Exception as e:
            print("Failed to export unitary file:", e)

    # -----------------------------------
    # 4) Common unitaries
    # -----------------------------------
    def fill_identity(self):
        """Fill the NxN entry boxes with the identity unitary."""
        n = self.n
        I = np.eye(n, dtype=complex)
        self.fill_unitary_entries(I)

    def fill_haar_random(self):
        """Fill with a Haar-random unitary."""
        n = self.n
        U = haar_random_unitary(n)
        self.fill_unitary_entries(U)

    # -----------------------------------
    # Helper: read NxN from the entries
    # -----------------------------------
    def read_unitary_entries(self) -> np.ndarray:
        """Reads the text from each entry, returns NxN array (complex)."""
        n = self.n
        unitary_data = []
        for i in range(n):
            row_vals = []
            for j in range(n):
                val_str = self.unitary_entries[i][j].get().strip()
                if not val_str:
                    val_str = "0"
                try:
                    val = complex(val_str)  # or float(val_str) if real only
                except ValueError:
                    print(f"Invalid entry at row={i}, col={j}: {val_str}")
                    return None
                row_vals.append(val)
            unitary_data.append(row_vals)
        return np.array(unitary_data, dtype=complex)

    def fill_unitary_entries(self, U: np.ndarray):
        """
        Fill the NxN entries from a unitary U, automatically truncated if bigger.
        """
        n = min(self.n, U.shape[0], U.shape[1])  # in case the user loaded a bigger unitary
        for i in range(n):
            for j in range(n):
                val = U[i, j]
                # If purely real, optional to store as real
                # For a complex number, e.g. '0.123+0.456j'
                val_str = f"{val.real:.4f}"
                if abs(val.imag) > 1e-12:
                    sign = "+" if val.imag >= 0 else "-"
                    val_str = f"{val.real:.4f}{sign}{abs(val.imag):.4f}j"
                self.unitary_entries[i][j].delete(0, "end")
                self.unitary_entries[i][j].insert(0, val_str)