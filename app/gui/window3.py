# app/gui/window3.py

from app.imports import *
import tkinter.filedialog as filedialog
import numpy as np

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
        self.tabview = ctk.CTkTabview(self.right_frame, width=600, height=400)
        self.tabview.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        self.tabview.add('U1')
        self.tabview.add('U2')
        self.tabview.add('U3')

        # For each tab, build a separate NxN of CTkEntries.
        self.unitary_entries_U1 = self.build_nxn_tab(self.tabview.tab('U1'))
        self.unitary_entries_U2 = self.build_nxn_tab(self.tabview.tab('U2'))
        self.unitary_entries_U3 = self.build_nxn_tab(self.tabview.tab('U3'))

        # Bottom buttons
        self.bottom_buttons_frame = ctk.CTkFrame(self.right_frame, fg_color='transparent')
        self.bottom_buttons_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)

        self.apply_unitary_button = ctk.CTkButton(
            self.bottom_buttons_frame, text='Decompose',
            command=self.decompose_unitary
        )
        self.apply_unitary_button.pack(fill='x', pady=(5,5))

        self.import_unitary_button = ctk.CTkButton(
            self.bottom_buttons_frame, text='Import Unitary',
            command=self.import_unitary_file
        )
        self.import_unitary_button.pack(fill='x', pady=(5,5))

        self.export_unitary_button = ctk.CTkButton(
            self.bottom_buttons_frame, text='Export Unitary',
            command=self.export_unitary_file
        )
        self.export_unitary_button.pack(fill='x', pady=(5,5))

        # Common unitaries
        self.common_unitaries_frame = ctk.CTkFrame(self.bottom_buttons_frame, fg_color='transparent')
        self.common_unitaries_frame.pack(fill='x', pady=(5,5))

        self.identity_button = ctk.CTkButton(
            self.common_unitaries_frame, text='Identity',
            command=self.fill_identity
        )
        self.identity_button.pack(side='left', expand=True, fill='x', padx=2)

        self.random_button = ctk.CTkButton(
            self.common_unitaries_frame, text='Random',
            command=self.fill_random
        )
        self.random_button.pack(side='left', expand=True, fill='x', padx=2)

        # Load any saved unitary from AppData for each tab
        self.load_all_tabs()

    def get_active_tab(self):
        '''
        Returns the unitary entry grid (2D list) and corresponding AppData variable
        for the currently selected tab.
        '''
        current_tab = self.tabview.get()
    
        if current_tab == 'U1':
            return self.unitary_entries_U1, 'saved_unitary_U1'
        elif current_tab == 'U2':
            return self.unitary_entries_U2, 'saved_unitary_U2'
        elif current_tab == 'U3':
            return self.unitary_entries_U3, 'saved_unitary_U3'
        
    def get_unitary_by_tab(self, tab_name):
        '''
        Returns the unitary entry grid (2D list) and corresponding AppData variable
        for a specific tab (U1, U2, U3).
        '''
        if tab_name == 'U1':
            return self.unitary_entries_U1, 'saved_unitary_U1'
        elif tab_name == 'U2':
            return self.unitary_entries_U2, 'saved_unitary_U2'
        elif tab_name == 'U3':
            return self.unitary_entries_U3, 'saved_unitary_U3'
     
    def load_all_tabs(self):
        '''Fill each tab's NxN from its corresponding AppData matrix.'''
        for tab_name in ['U1', 'U2', 'U3']:
            # Get the NxN entry grid and AppData variable dynamically
            entries, appdata_var = self.get_unitary_by_tab(tab_name)
    
            if entries is not None and appdata_var is not None:
                # Load saved matrix or default to zeros
                unitary_matrix = getattr(AppData, appdata_var, None)
                if unitary_matrix is None:
                    unitary_matrix = np.eye(self.n, dtype=complex)
    
                self.fill_tab_entries(entries, unitary_matrix)

    def save_all_tabs(self):
        '''Read NxN from each tab's 2D list and store it in AppData dynamically.'''
        for tab_name in ['U1', 'U2', 'U3']:
            entries, appdata_var = self.get_unitary_by_tab(tab_name)
    
            if entries is not None and appdata_var is not None:
                unitary_matrix = self.read_tab_entries(entries)
                if unitary_matrix is not None:
                    setattr(AppData, appdata_var, unitary_matrix)  

    def build_nxn_tab(self, parent_frame):
        '''Create an NxN grid of CTkEntry inside parent_frame, return 2D list.'''
        entries_2d = []
        # A container in each tab for the NxN
        frame = ctk.CTkFrame(parent_frame, fg_color='gray20')
        frame.pack(anchor='center', padx=5, pady=5)

        for i in range(self.n):
            row_entries = []
            for j in range(self.n):
                e = ctk.CTkEntry(frame, width=55)
                e.grid(row=i, column=j, padx=2, pady=2)
                row_entries.append(e)
            entries_2d.append(row_entries)
        return entries_2d

    def read_tab_entries(self, entries_2d) -> np.ndarray | None:
        '''Returns NxN complex array from the given 2D entries, or None on error.'''
        data = []
        for i in range(self.n):
            row_vals = []
            for j in range(self.n):
                val_str = entries_2d[i][j].get().strip()
                if not val_str:
                    val_str = '0'
                try:
                    val = complex(val_str)
                except ValueError:
                    print(f'Invalid entry at row={i}, col={j}: {val_str}')
                    return None
                row_vals.append(val)
            data.append(row_vals)
        return np.array(data, dtype=complex)

    def fill_tab_entries(self, entries_2d, matrix: np.ndarray):
        '''Fill the NxN entries_2d from 'matrix'.'''
        rows = min(self.n, matrix.shape[0])
        cols = min(self.n, matrix.shape[1])
        for i in range(rows):
            for j in range(cols):
                val = matrix[i, j]
                val_str = f'{val.real:.4f}'
                if abs(val.imag) > 1e-12:
                    sign = '+' if val.imag >= 0 else '-'
                    val_str = f'{val.real:.4f}{sign}{abs(val.imag):.4f}j'
                entries_2d[i][j].delete(0, 'end')
                entries_2d[i][j].insert(0, val_str)

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
        '''
        Refresh all unitary matrices when the user selects a new mesh size.
        This function re-creates the entry widgets inside each tab’s container,
        preserving the container (which was created using pack).
        '''
        # Parse new NxN dimension
        self.n = int(new_mesh_size.split('x')[0])
        
        for tab_name in ['U1', 'U2', 'U3']:
            # Get the current tab's entries and associated AppData variable
            entries, appdata_var = self.get_unitary_by_tab(tab_name)
            if entries is None or appdata_var is None:
                continue
    
            # Determine the container frame that holds the NxN entries.
            # We assume at least one entry exists; if not, use the tab's frame.
            if entries and entries[0]:
                container = entries[0][0].master
            else:
                container = self.tabview.tab(tab_name)
            
            # Destroy all children in the container (the old entry widgets)
            for child in container.winfo_children():
                child.destroy()
            # Clear the stored entries list
            entries.clear()
    
            # Rebuild the NxN grid in the same container using grid (not pack)
            new_entries = []
            for i in range(self.n):
                row_entries = []
                for j in range(self.n):
                    e = ctk.CTkEntry(container, width=40)
                    e.grid(row=i, column=j, padx=2, pady=2)
                    row_entries.append(e)
                new_entries.append(row_entries)
            
            # Update the corresponding attribute for this tab
            if tab_name == 'U1':
                self.unitary_entries_U1 = new_entries
            elif tab_name == 'U2':
                self.unitary_entries_U2 = new_entries
            elif tab_name == 'U3':
                self.unitary_entries_U3 = new_entries
    
            # Load saved values if available; otherwise, default to an identity matrix
            unitary_matrix = getattr(AppData, appdata_var, None)
            if unitary_matrix is None or unitary_matrix.shape[0] != self.n or unitary_matrix.shape[1] != self.n:
                unitary_matrix = np.eye(self.n, dtype=complex)
            
            self.fill_tab_entries(new_entries, unitary_matrix)
            setattr(AppData, appdata_var, unitary_matrix)      