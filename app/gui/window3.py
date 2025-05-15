# app/gui/window3.py

from app.imports import *
import tkinter.filedialog as filedialog
import copy
from app.utils.qontrol.qmapper8x8 import create_label_mapping, apply_grid_mapping
from app.utils.unitary import mzi_lut
from app.utils.unitary import mzi_convention
from app.utils.appdata import AppData
from datetime import datetime

class Window3Content(ctk.CTkFrame):
    
    def __init__(self, master, channel, fit, IOconfig, app, qontrol, thorlabs, daq, grid_size = "8x8", **kwargs):
        super().__init__(master, **kwargs)
        self.channel = channel
        self.fit = fit
        self.IOconfig = IOconfig
        self.app = app
        self.qontrol = qontrol
        self.thorlabs = thorlabs
        self.daq = daq

        # NxN dimension
        self.n = int(grid_size.split('x')[0])
        self.grid_size = grid_size 

        # Main layout
        self.content_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.content_frame.pack(expand=True, fill='both', padx=2, pady=2)

        self.right_frame = ctk.CTkFrame(self.content_frame, fg_color='transparent')
        self.right_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        # Create a Tabview
        self.tabview = ctk.CTkTabview(self.right_frame, width=600, height=300)
        self.tabview.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        # Add a tab for a unitary matrix
        self.tabview.add('Unitary')

        # For each tab, build a separate NxN of CTkEntries.
        self.unitary_entries = self.create_nxn_entries(self.tabview.tab('Unitary'))

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

        # Create button frame using pack
        button_frame = ctk.CTkFrame(self.bottom_buttons_frame, fg_color='transparent')
        button_frame.pack(anchor='center', pady=(5, 5))

        # Add the cycle unitary button
        self.cycle_unitaries_button = ctk.CTkButton(
            button_frame,
            text="Cycle Unitaries",
            command=self.cycle_unitaries,
            width=120,
            height=30
        )
        self.cycle_unitaries_button.pack(side='left', padx=5, pady=5)

        # Add the dwell time label and entry next to the button
        self.dwell_label = ctk.CTkLabel(button_frame, text="Dwell Time (s):")
        self.dwell_label.pack(side='left', padx=5)

        self.dwell_entry = ctk.CTkEntry(button_frame, width=100)
        self.dwell_entry.insert(0, "0.5")  # default
        self.dwell_entry.pack(side='left', padx=5)

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

    def _read_all_daq_channels(self):
        """
        Lists all available AI channels on the DAQ device,
        reads averaged voltage for each channel, and displays them in the text box.
        """
        lines = []

        if not self.daq:
            lines.append("No device found.")
            self._daq_last_result = "\n".join(lines)
            return

        channels = self.daq.list_ai_channels()
        if not channels:
            lines.append("No device found.")
            self._daq_last_result = "\n".join(lines)
            return
        
        try:
            num_samples = int(self.samples_entry.get())   # Fails here with ValueError
            if num_samples <= 0:
                raise ValueError("Sample count must be positive.")
        except Exception as e:
            print(f"[DAQ] Invalid sample count input: {e}")  # Now safe
            num_samples = 10
            self.samples_entry.delete(0, "end")
            self.samples_entry.insert(0, str(num_samples))

        readings = self.daq.read_power(channels=channels, samples_per_channel=num_samples, unit=self.selected_unit)
        if readings is None:
            lines.append("Failed to read from DAQ or DAQ not connected.")
            self._daq_last_result = "\n".join(lines)
            return

        # Normalize to list for consistent processing
        if isinstance(readings, float):
            readings = [readings]  # wrap float in list if only one channel

        # Build text output
        lines = []
        for ch_name, voltage in zip(channels, readings):
            lines.append(f"{ch_name} -> {voltage} {self.selected_unit}")

        # Save this part to combine with Thorlabs 
        self._daq_last_result = "\n".join(lines)    

        '''
            # ---- Thorlabs measurements => site3
            thorlabs_vals = 0.0
            if self.thorlabs:
                if isinstance(self.thorlabs, list):
                    device = self.thorlabs[0]  # or pick whichever you want
                else:
                    device = self.thorlabs

                try:
                    thorlabs_vals = device.read_power(unit="uW")
                except Exception as e:
                    print(f"Thorlabs read error: {e}")
        '''

    def cycle_unitaries(self):
        """
        1) Prompts user to select folder containing .npy files
        2) Loads each .npy file in sequence, assigns to U_step, processes it
        3) Applies phases, measures output power continuously during dwell time, saves averaged results
        """
        try:
            # Get dwell time and setup sampling parameters
            dwell = float(self.dwell_entry.get())
            sample_rate = 1000  # Hz
            samples_per_channel = int(dwell * sample_rate)  # Total samples to collect during dwell

            # Prompt for folder selection
            folder_path = filedialog.askdirectory(title="Select Folder Containing Unitary Step Files")
            if not folder_path:
                print("No folder selected. Aborting.")
                return

            npy_files = sorted(
                [f for f in os.listdir(folder_path) if f.endswith(".npy") and f.startswith("step_")],
                key=lambda x: int(x.split("_")[1].split(".")[0])  # Extract number from 'step_1.npy'
            )
            if not npy_files:
                print("No unitary step files found in selected folder.")
                return

            # Prepare results storage
            results = []
            headers = ["timestamp", "step", "site1", "site2", "site3", "site4"]

            # Process each unitary file
            for step_idx, npy_file in enumerate(npy_files, start=1):
                file_path = os.path.join(folder_path, npy_file)
                print(f"\nProcessing step {step_idx}: {npy_file}")

                # Load unitary
                try:
                    U_step = np.load(file_path)
                except Exception as e:
                    print(f"Error loading {npy_file}: {e}")
                    continue

                # Decompose unitary
                
                try:
                    I = itf.square_decomposition(U_step)
                    bs_list = I.BS_list
                    mzi_convention.clements_to_chip(bs_list)
                    setattr(AppData, 'default_json_grid', mzi_lut.get_json_output(self.n, bs_list))
                except Exception as e:
                    print(f"Error in decomposition: {e}")
                    continue
            
                # Apply phases
                self.apply_phase_new()

                # DAQ measurements with continuous sampling during dwell time
                daq_values = [0.0, 0.0, 0.0, 0.0]
                if self.daq and self.daq.list_ai_channels():
                    channels = ["Dev1/ai0", "Dev1/ai1", "Dev1/ai2", "Dev1/ai3", "Dev1/ai4"]
                    try:
                        # Read power continuously during dwell time
                        daq_vals = self.daq.read_power(
                            channels=channels,
                            samples_per_channel=samples_per_channel,
                            sample_rate=sample_rate,
                            unit='uW'
                        )

                        # Process and average the readings
                        if isinstance(daq_vals, list) and len(daq_vals) >= 2:
                            if isinstance(daq_vals[0], list):  # Multiple samples per channel
                                # Calculate mean for each channel
                                daq_values = [
                                    sum(ch_samples)/len(ch_samples) 
                                    for ch_samples in daq_vals
                                ]
                            else:  # Single sample per channel
                                daq_values = daq_vals

                        # Clear DAQ task
                        self.daq.clear_task()

                    except Exception as e:
                        print(f"Error reading DAQ: {e}")
                        daq_values = [0.0, 0.0, 0.0, 0.0]

                # Record results with timestamp
                current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                row = [current_timestamp, step_idx, daq_values[0], daq_values[1], daq_values[2], daq_values[3]]
                results.append(row)
                
                # Print current values
                print(f"Step {step_idx} measurements:")
                print(f"  Site 1: {daq_values[0]:.3f} µW")
                print(f"  Site 2: {daq_values[1]:.3f} µW")
                print(f"  Site 3: {daq_values[2]:.3f} µW")
                print(f"  Site 4: {daq_values[3]:.3f} µW")

            # Export results
            if results:
                self._export_results_to_csv(results, headers)
                print("\nFinished cycling unitaries!")
                
                # Reset phases to zero
                zero_config = self._create_zero_config()
                apply_grid_mapping(self.qontrol, zero_config, self.grid_size)
                print("All values reset to zero")
            else:
                print("\nNo results collected during experiment")

        except Exception as e:
            print(f"Experiment failed: {e}")
            import traceback
            traceback.print_exc()

    def _create_zero_config(self):
        """Create a configuration with all theta and phi values set to zero"""
        n = int(self.grid_size.split('x')[0])
        zero_config = {}
        
        # Generate all possible crosspoint labels (A1, A2, B1, etc.)
        for row in range(n):
            row_letter = chr(65 + row)  # A, B, C, etc.
            for col in range(1, n+1):
                cross_label = f"{row_letter}{col}"
                zero_config[cross_label] = {
                    "arms": ["TL", "TR", "BL", "BR"],  # Include all arms
                    "theta": "0",
                    "phi": "0"
                }
        
        return json.dumps(zero_config)

    def apply_phase_new(self):
        """
        Apply phase settings to the entire grid based on phase calibration data.
        Processes all theta and phi values in the current grid configuration.
        """
        try:
            # Get current grid configuration
            grid_config = AppData.default_json_grid
            print(grid_config)
            if not grid_config:
                print("No grid configuration found")
                return
                
            # Create label mapping for channel assignments
            label_map = create_label_mapping(8)  # Assuming 8x8 grid
            
            # Create a new configuration with current values
            phase_grid_config = copy.deepcopy(grid_config)
            
            # Track successful and failed applications
            applied_channels = []
            failed_channels = []
            
            # Process each cross in the grid
            for cross_label, data in grid_config.items():
                # Skip if this cross isn't in our mapping
                if cross_label not in label_map:
                    continue
                    
                theta_ch, phi_ch = label_map[cross_label]
                theta_val = data.get("theta", "0")
                phi_val = data.get("phi", "0")

                # Process theta channel
                if theta_ch is not None and theta_val:
                    try:
                        theta_float = float(theta_val)
                        current_theta = self._calculate_current_for_phase(theta_ch, theta_float, "cross", "bar")
                        if current_theta is not None:
                            # Quantize to 5 decimal places
                            current_theta = round(current_theta, 5)
                            # Update the phase_grid_config with current value
                            phase_grid_config[cross_label]["theta"] = str(current_theta)  # Store in A
                            applied_channels.append(f"{cross_label}:θ = {current_theta:.5f} mA")
                        else:
                            failed_channels.append(f"{cross_label}:θ (no calibration)")
                    except Exception as e:
                        failed_channels.append(f"{cross_label}:θ ({str(e)})")

                # Process phi channel
                if phi_ch is not None and phi_val:
                    try:
                        phi_float = float(phi_val)
                        current_phi = self._calculate_current_for_phase(phi_ch, phi_float, "cross", "bar")
                        if current_phi is not None:
                            # Quantize to 5 decimal places
                            current_phi = round(current_phi, 5)
                            # Update the phase_grid_config with current value
                            phase_grid_config[cross_label]["phi"] = str(current_phi)  # Store in A
                            applied_channels.append(f"{cross_label}:φ = {current_phi:.5f} mA")
                        else:
                            failed_channels.append(f"{cross_label}:φ (no calibration)")
                    except Exception as e:
                        failed_channels.append(f"{cross_label}:φ ({str(e)})")
            
            # Store the phase grid config for later use
            self.phase_grid_config = phase_grid_config
            
            # Only show error message if there are failures
            if failed_channels:
                result_message = f"Failed to apply to {len(failed_channels)} channels"
                print(result_message)
                print("Failed channels:", failed_channels)
                
            # Debugging: Print the grid size
            print(f"Grid size: {self.grid_size}")
            
            try:
                config_json = json.dumps(phase_grid_config)
                apply_grid_mapping(self.qontrol, config_json, self.grid_size)
            except Exception as e:
                print(f"Device update failed: {str(e)}")        

            return phase_grid_config
            
        except Exception as e:
            print(f"Failed to apply phases: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
                
    def _calculate_current_for_phase(self, channel, phase_value, *io_configs):
        """
        Calculate current for a given phase value, trying multiple IO configurations.
        Returns current in mA or None if calculation fails.
        """
        # Try each IO configuration in order until one works
        for io_config in io_configs:
            # Check for cross calibration data
            if io_config == "cross" and channel < len(self.app.caliparamlist_lincub_cross) and self.app.caliparamlist_lincub_cross[channel] != "Null":
                params = self.app.caliparamlist_lincub_cross[channel]
                return self._calculate_current_from_params(channel, phase_value, params)
                
            # Check for bar calibration data
            elif io_config == "bar" and channel < len(self.app.caliparamlist_lincub_bar) and self.app.caliparamlist_lincub_bar[channel] != "Null":
                params = self.app.caliparamlist_lincub_bar[channel]
                return self._calculate_current_from_params(channel, phase_value, params)
        
        return None

    def _calculate_current_from_params(self, channel, phase_value, params):
        """Calculate current from phase parameters"""
        # Extract calibration parameters
        A = params['amp']
        b = params['omega']
        c = params['phase']
        d = params['offset']
        
        '''
        # Find the positive phase the heater must add 
        delta_phase = (phase_value % 2) * np.pi

        # Calculate the heating power for this phase shift
        P = delta_phase / b
        '''
        
        phase_value_offset = phase_value
        # Check if phase is within valid range
        if phase_value < c/np.pi:
            print(f"Warning: Phase {phase_value}π is less than offset phase {c/np.pi}π for channel {channel}")
            # Add phase_value by 2 and continue with calculation
            phase_value_offset  = phase_value + 2
            
            print(f"Using adjusted phase value: {phase_value_offset}π")

        # Calculate heating power for this phase shift
        P = abs((phase_value_offset*np.pi - c) / b)
        
        
        # Get resistance parameters
        if channel < len(self.app.resistance_parameter_list):
            r_params = self.app.resistance_parameter_list[channel]
            
            # Use cubic+linear model if available
            if len(r_params) >= 2:
                # Define symbols for solving equation
                I = sp.symbols('I')
                P_watts = P/1000  # Convert to watts
                R0 = r_params[1]  # Linear resistance term (c)
                alpha = r_params[0]/R0 if R0 != 0 else 0  # Nonlinearity parameter (a/c)
                
                # Define equation: P/R0 = I^2 + alpha*I^4
                eq = sp.Eq(P_watts/R0, I**2 + alpha*I**4)
                
                # Solve the equation
                solutions = sp.solve(eq, I)
                
                # Filter and choose the real, positive solution
                positive_solutions = [sol.evalf() for sol in solutions if sol.is_real and sol.evalf() > 0]
                if positive_solutions:
                    return float(1000 * positive_solutions[0])  # Convert to mA 
                else:
                    # Fallback to linear model
                    R0 = r_params[1]
                    return float(round(1000 * np.sqrt(P/(R0*1000)), 2))
            else:
                # Use linear model
                R = self.app.linear_resistance_list[channel] if channel < len(self.app.linear_resistance_list) else 50.0
                return float(round(1000 * np.sqrt(P/(R*1000)), 2))
        else:
            # No resistance parameters, use default
            return float(round(1000 * np.sqrt(P/(50.0*1000)), 2))

    def get_unitary_mapping(self):
        '''Returns the entry grid and AppData variable for the unitary tab.'''
        return self.unitary_entries, 'saved_unitary'

    def get_active_tab(self):
        '''
        Returns the unitary entry grid (2D list) and corresponding AppData variable
        for the currently selected tab.
        '''
        return self.get_unitary_mapping()  
        
    def get_unitary_by_tab(self, tab_name):
        '''
        Returns the unitary entry grid (2D list) and corresponding AppData variable
        for a specific tab (U1, U2, U3).
        '''
        return self.get_unitary_mapping().get(tab_name, (None, None))
     
    def handle_all_tabs(self, operation='load'):
        '''Handles loading or saving of the unitary matrix.'''
        entries, appdata_var = self.get_unitary_mapping()  # Directly unpack the tuple
        if entries is None or appdata_var is None:
            return  # Skip if invalid

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
            print(f'Error in {operation} operation: {e}')

    def create_nxn_entries(self, parent_frame):
        '''Creates an NxN grid of CTkEntry fields inside parent_frame and returns a 2D list.'''
        entries_2d = []
        frame = ctk.CTkFrame(parent_frame, fg_color='gray20')
        frame.pack(anchor='center', padx=5, pady=5)
    
        for i in range(self.n):
            row_entries = []
            for j in range(self.n):
                e = ctk.CTkEntry(frame, width=55)
                e.grid(row=i, column=j, padx=5, pady=5)
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
                val_str = f'{val.real}'
                if abs(val.imag) > 1e-12:
                    sign = '+' if val.imag >= 0 else '-'
                    val_str = f'{val.real}{sign}{abs(val.imag)}j'
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
            print(AppData.default_json_grid)

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

        # Get the single mapping
        entries, appdata_var = self.get_unitary_mapping()
        if entries is None or appdata_var is None:
            return  # Skip if invalid

        # Determine parent frame
        container = self.tabview.tab('Unitary')

        # Destroy old widgets and clear entries
        for child in container.winfo_children():
            child.destroy()

        # Recreate the grid and update reference
        new_entries = self.create_nxn_entries(container)
        setattr(self, 'unitary_entries', new_entries)

        # Restore saved matrix or default to identity
        unitary_matrix = getattr(AppData, appdata_var, None)
        if unitary_matrix is None or unitary_matrix.shape != (self.n, self.n):
            unitary_matrix = np.eye(self.n, dtype=complex)

        self.fill_tab_entries(new_entries, unitary_matrix)
        setattr(AppData, appdata_var, unitary_matrix)