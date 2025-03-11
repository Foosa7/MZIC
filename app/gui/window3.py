# app/gui/window3.py

from app.imports import *
import tkinter.filedialog as filedialog

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

        # NxN dimension
        self.n = int(grid_size.split('x')[0])

        # Main layout
        self.content_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.content_frame.pack(expand=True, fill='both', padx=2, pady=2)

        self.right_frame = ctk.CTkFrame(self.content_frame, fg_color='transparent')
        self.right_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        # Create a Tabview
        self.tabview = ctk.CTkTabview(self.right_frame, width=600, height=300)
        self.tabview.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        # Add a tab for each unitary 
        self.tabview.add('U1')
        self.tabview.add('U2')
        self.tabview.add('U3')

        # For each tab, build a "grid"—now implemented with a single text box:
        self.unitary_entries_U1 = self.create_nxn_entries(self.tabview.tab('U1'))
        self.unitary_entries_U2 = self.create_nxn_entries(self.tabview.tab('U2'))
        self.unitary_entries_U3 = self.create_nxn_entries(self.tabview.tab('U3'))

        # Bottom buttons
        self.bottom_buttons_frame = ctk.CTkFrame(self.right_frame, fg_color='transparent')
        self.bottom_buttons_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)

        self.apply_unitary_button = ctk.CTkButton(
            self.bottom_buttons_frame, text='Decompose',
            command=self.decompose_unitary
        )
        self.apply_unitary_button.pack(anchor='center', pady=(5,5))

        self.import_unitary_button = ctk.CTkButton(
            self.bottom_buttons_frame, text='Import Unitary',
            command=self.import_unitary_file
        )
        self.import_unitary_button.pack(anchor='center', pady=(5,5))

        self.export_unitary_button = ctk.CTkButton(
            self.bottom_buttons_frame, text='Export Unitary',
            command=self.export_unitary_file
        )
        self.export_unitary_button.pack(anchor='center', pady=(5,5))

        # Common unitaries
        self.common_unitaries_frame = ctk.CTkFrame(self.bottom_buttons_frame, fg_color='transparent')
        self.common_unitaries_frame.pack(anchor='center', pady=(5,5))

        self.identity_button = ctk.CTkButton(
            self.common_unitaries_frame, text='Identity',
            command=self.fill_identity
        )
        self.identity_button.pack(side='left', expand=True, anchor='center', padx=2)

        self.random_button = ctk.CTkButton(
            self.common_unitaries_frame, text='Random',
            command=self.fill_random
        )
        self.random_button.pack(side='left', expand=True, anchor='center', padx=2)

        # Load any saved unitary from AppData for each tab
        self.handle_all_tabs()

    def get_unitary_mapping(self):
        '''Returns a dictionary mapping tab names to their corresponding entry grids and AppData variables.'''
        return {
            'U1': (self.unitary_entries_U1, 'saved_unitary_U1'),
            'U2': (self.unitary_entries_U2, 'saved_unitary_U2'),
            'U3': (self.unitary_entries_U3, 'saved_unitary_U3'),
        }

    def get_active_tab(self):
        '''
        Returns the unitary entry grid (2D list / text widget) and corresponding AppData variable
        for the currently selected tab.
        '''
        return self.get_unitary_mapping().get(self.tabview.get(), (None, None))
        
    def get_unitary_by_tab(self, tab_name):
        '''
        Returns the unitary entry grid (2D list / text widget) and corresponding AppData variable
        for a specific tab (U1, U2, U3).
        '''
        return self.get_unitary_mapping().get(tab_name, (None, None))
     
    def handle_all_tabs(self, operation='load'):
        '''Handles loading or saving of unitary matrices for all tabs based on the operation.'''
        for tab_name, (entries, appdata_var) in self.get_unitary_mapping().items():
            if entries is None or appdata_var is None:
                continue  # Skip invalid entries
            try:
                if operation == 'load':
                    unitary_matrix = getattr(AppData, appdata_var, None)
                    if unitary_matrix is None or not isinstance(unitary_matrix, np.ndarray):
                        unitary_matrix = np.eye(self.n, dtype=complex)  # Default to identity
                    self.fill_tab_entries(entries, unitary_matrix)
                
                elif operation == 'save':
                    unitary_matrix = self.read_tab_entries(entries)
                    if unitary_matrix is not None:
                        setattr(AppData, appdata_var, unitary_matrix)
            except Exception as e:
                print(f'Error in {operation} operation for {tab_name}: {e}')  # Log error 

    def create_nxn_entries(self, parent_frame):
        '''
        Creates an NxN "grid" of CTkEntry fields.
        '''
        matrix_textbox = ctk.CTkTextbox(parent_frame, width=800, height=200)
        matrix_textbox.pack(anchor='center', padx=5, pady=5)
        return matrix_textbox

    def read_tab_entries(self, entries_2d) -> np.ndarray | None:
        '''
        Returns an NxN complex array parsed from the given 2D entries.
        '''
        text_content = entries_2d.get("1.0", "end").strip()
        if not text_content:
            return None
        
        lines = text_content.splitlines()
        if len(lines) != self.n:
            print(f"Expected {self.n} rows, found {len(lines)} lines.")
            return None
        
        data = []
        for row_index, line in enumerate(lines):
            parts = line.split()
            if len(parts) != self.n:
                print(f"Line {row_index} has {len(parts)} columns, expected {self.n}.")
                return None
            
            row_vals = []
            for val_str in parts:
                try:
                    val = complex(val_str)
                except ValueError:
                    print(f"Invalid complex format '{val_str}' in row {row_index}.")
                    return None
                row_vals.append(val)
            data.append(row_vals)

        return np.array(data, dtype=complex)

    def fill_tab_entries(self, entries_2d, matrix: np.ndarray):
        '''
        Fill the NxN entries_2d from 'matrix'.
        '''
        rows = min(self.n, matrix.shape[0])
        cols = min(self.n, matrix.shape[1])
        lines = []

        for i in range(rows):
            row_vals = []
            for j in range(cols):
                val = matrix[i, j]
                if abs(val.imag) < 1e-12:
                    row_vals.append(f'{val.real:.4f}')
                else:
                    sign = '+' if val.imag >= 0 else '-'
                    row_vals.append(f'{val.real:.4f}{sign}{abs(val.imag):.4f}j')
            lines.append(" ".join(row_vals))

        entries_2d.configure(state='normal')
        entries_2d.delete("1.0", "end")
        entries_2d.insert("1.0", "\n".join(lines))
        entries_2d.configure(state='normal')

    def decompose_unitary(self):
        '''Read NxN from the currently selected tab and decompose it.'''
        entries, appdata_var = self.get_active_tab()  # Get the active tab's unitary
    
        # Read the matrix from the selected tab
        matrix_u = self.read_tab_entries(entries)
        if matrix_u is None:
            return
    
        try:
            # Perform decomposition
            I = itf.square_decomposition(matrix_u)
            bs_list = I.BS_list
            mzi_convention.clements_to_chip(bs_list)
    
            # Store the decomposition result in AppData
            setattr(AppData, 'default_json_grid', mzi_lut.get_json_output(self.n, bs_list))
    
        except Exception as e:
            print('Error in decomposition:', e)
    
    def import_unitary_file(self):
        '''Import an .npy unitary file into the currently selected tab.'''
        path = filedialog.askopenfilename(
            title='Select Unitary File',
            filetypes=[('NumPy files', '*.npy')]  # Only allow .npy
        )
        if not path:
            return
    
        try:
            mat = np.load(path)  # Load NumPy matrix
    
            # Get the active tab's NxN and AppData variable
            entries, appdata_var = self.get_active_tab()
            
            if entries is not None and appdata_var is not None:
                self.fill_tab_entries(entries, mat)
                setattr(AppData, appdata_var, mat)  # Save dynamically
        except Exception as e:
            print('Failed to import unitary file:', e)
    
    def export_unitary_file(self):
        '''Export the currently selected tab's unitary as a .npy file.'''
        entries, _ = self.get_active_tab()  # Get the active tab's NxN entries
    
        if entries is None:
            print('Error: No valid tab selected for export.')
            return
    
        matrix = self.read_tab_entries(entries)
        if matrix is None:
            print('No valid matrix found for export.')
            return
    
        path = filedialog.asksaveasfilename(
            title='Save Unitary File',
            defaultextension='.npy',
            filetypes=[('NumPy files', '*.npy')]  # Only allow .npy
        )
        if not path:
            return
    
        try:
            np.save(path, matrix)
            print(f'Unitary saved successfully to {path}.')
        except Exception as e:
            print('Failed to export unitary file:', e)

    def fill_identity(self):
        '''Fill the currently selected tab with an identity matrix.'''
        mat = np.eye(self.n, dtype=complex)
    
        entries, appdata_var = self.get_active_tab()  
    
        if entries is not None and appdata_var is not None:
            self.fill_tab_entries(entries, mat)
            setattr(AppData, appdata_var, mat)  # Save dynamically

    def fill_random(self):
        '''Fill the currently selected tab with a random unitary matrix.'''
        mat = itf.random_unitary(self.n)
    
        entries, appdata_var = self.get_active_tab()  # Get active tab dynamically
    
        if entries is not None and appdata_var is not None:
            self.fill_tab_entries(entries, mat)
            setattr(AppData, appdata_var, mat)  # Save dynamically

    def update_grid(self, new_mesh_size):
        '''Refresh NxN grids when the user selects a new mesh size.'''
        self.n = int(new_mesh_size.split('x')[0])
        
        for tab_name, (entries, appdata_var) in self.get_unitary_mapping().items():
            if entries is None or appdata_var is None:
                continue
    
            # Determine parent frame
            container = self.tabview.tab(tab_name)
    
            # Destroy old widgets and clear entries
            for child in container.winfo_children():
                child.destroy()
    
            # Recreate the "grid" and update reference
            new_entries = self.create_nxn_entries(container)
            setattr(self, f'unitary_entries_{tab_name}', new_entries)
    
            # Restore saved matrix or default to identity
            unitary_matrix = getattr(AppData, appdata_var, None)
            if unitary_matrix is None or unitary_matrix.shape != (self.n, self.n):
                unitary_matrix = np.eye(self.n, dtype=complex)
    
            self.fill_tab_entries(new_entries, unitary_matrix)
            setattr(AppData, appdata_var, unitary_matrix)
