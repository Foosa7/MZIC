# app/gui/window3.py
from app.imports import *

import tkinter.simpledialog as simpledialog
import tkinter.filedialog as filedialog
from app.utils import grid  
from app.utils.unitary import mzi_lut
from app.utils.unitary import mzi_convention
from app.utils.appdata import AppData

class Window3Content(ctk.CTkFrame):
    
    def __init__(self, master, channel, fit, IOconfig, app, qontrol, grid_size, **kwargs):
        super().__init__(master, **kwargs)
        self.channel = channel
        self.fit = fit
        self.IOconfig = IOconfig
        self.app = app
        self.qontrol = qontrol
        self.grid_size = grid_size
        
        # Determine dimension n from mesh size
        self.n = int(self.grid_size.split('x')[0])
        
        # -- Main content layout --
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(expand=True, fill="both", padx=2, pady=2)
        
        # Right: controls
        self.right_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # =====================================
        #  Centered unitary panel
        # =====================================
        # A container to center the unitary
        self.unitary_container = ctk.CTkFrame(self.right_frame, fg_color="gray25")
        self.unitary_container.pack(fill="both", expand=True, padx=5, pady=(10,5))
        
        # We'll nest the actual grid of entries in a sub‐frame.
        # Pack or grid it with anchor='center' to center it.
        self.unitary_entries_frame = ctk.CTkFrame(self.unitary_container, fg_color="gray20")
        self.unitary_entries_frame.pack(anchor="center", padx=5, pady=5)
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

        # Random
        self.random_button = ctk.CTkButton(
            self.common_unitaries_frame, text="Random",
            command=self.fill_random
        )
        self.random_button.pack(side="left", expand=True, fill="x", padx=2)



    def update_grid(self, new_mesh_size):
        '''
        Refresh the matrix if the user picks a new mesh size
        '''
        
        # Parse out the new dimension.
        self.n = int(new_mesh_size.split('x')[0])
        
        # 1) Destroy old entry widgets
        for row in self.unitary_entries:
            for e in row:
                e.destroy()
        self.unitary_entries.clear()
    
        # 2) Rebuild NxN matrix
        for i in range(self.n):
            row_entries = []
            for j in range(self.n):
                entry = ctk.CTkEntry(self.unitary_entries_frame, width=40)
                entry.grid(row=i, column=j, padx=2, pady=2)
                row_entries.append(entry)
            self.unitary_entries.append(row_entries)
        
    # -----------------------------------
    # 1) “Apply Unitary” – read NxN from entries, decompose
    # -----------------------------------
    
    def apply_unitary_and_decompose(self):
        U = self.read_unitary_entries()
        if U is None:
            return
        try:
            # Create interferometer using Clements decomposition
            I = itf.square_decomposition(U)
            
            # Get beam splitter list in Clements convention
            bs_list = I.BS_list  
            
            # Convert angles from Clements MZI convention to Chip MZI convention
            mzi_convention.clements_to_chip(bs_list)
            
            # Generate JSON from mzi_lut.py
            AppData.default_json_grid = mzi_lut.get_json_output(self.n, bs_list)
            
            # Update GUI
            self.custom_grid.import_paths_json(AppData.default_json_grid)
            #self.custom_grid.update_selection()
            
        except Exception as e:
            print("Error in decomposition:", e)
            raise  # Optional: Reraise for debugging

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

    def fill_random(self):
        """Fill with a random unitary."""
        n = self.n
        U = itf.random_unitary(n)
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