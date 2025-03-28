# app/gui/window3.py

from app.imports import *
import tkinter.filedialog as filedialog
import math
import copy
from app.utils.qontrol.qmapper8x8 import create_label_mapping, apply_grid_mapping
from app.utils.unitary import mzi_lut
from app.utils.unitary import mzi_convention
from app.utils.appdata import AppData

class Window3Content(ctk.CTkFrame):
    
    def __init__(self, master, channel, fit, IOconfig, app, qontrol, daq, grid_size = "8x8", **kwargs):
        super().__init__(master, **kwargs)
        self.channel = channel
        self.fit = fit
        self.IOconfig = IOconfig
        self.app = app
        self.qontrol = qontrol
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

        # Add a tab for each unitary 
        self.tabview.add('U1')
        self.tabview.add('U2')
        self.tabview.add('U3')

        # For each tab, build a separate NxN of CTkEntries.
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

        ### Artificial Magnetic Field Controls ###
        self.amf_frame = ctk.CTkFrame(self.content_frame)
        self.amf_frame.grid(row=0, column=1, sticky='nsew', padx=20, pady=10)  # Place to the right side

        self.amf_label = ctk.CTkLabel(self.amf_frame, text="Artificial Magnetic Field") # Title
        self.amf_label.pack(pady=(0,10))

        # c (hopping amplitude)
        self.c_label = ctk.CTkLabel(self.amf_frame, text="Hopping (c):")
        self.c_label.pack()
        self.c_entry = ctk.CTkEntry(self.amf_frame, width=100)
        self.c_entry.insert(0, "1.0")  # default
        self.c_entry.pack(pady=(0,10))

        # Rabi cycles
        self.rabi_label = ctk.CTkLabel(self.amf_frame, text="Rabi Half-Cycles:")
        self.rabi_label.pack()
        self.rabi_entry = ctk.CTkEntry(self.amf_frame, width=100)
        self.rabi_entry.insert(0, "1")  # default
        self.rabi_entry.pack(pady=(0,10))

        # Total time entry (only used in "total" mode)
        self.time_label = ctk.CTkLabel(self.amf_frame, text="Total Time (s):")
        self.time_label.pack()
        self.time_entry = ctk.CTkEntry(self.amf_frame, width=100)
        self.time_entry.insert(0, "1.0")
        self.time_entry.pack(pady=(0, 10))

        # N (Time steps)
        self.N_label = ctk.CTkLabel(self.amf_frame, text="Time Steps (N):")
        self.N_label.pack()
        self.N_entry = ctk.CTkEntry(self.amf_frame, width=100)
        self.N_entry.insert(0, "5")  # default
        self.N_entry.pack(pady=(0,10))

        # Direction (CW or CCW)
        self.direction_var = ctk.StringVar(value="CW")
        self.cw_radio = ctk.CTkRadioButton(self.amf_frame, text="CW", variable=self.direction_var, value="CW")
        self.ccw_radio = ctk.CTkRadioButton(self.amf_frame, text="CCW", variable=self.direction_var, value="CCW")
        self.cw_radio.pack(pady=(0,5))
        self.ccw_radio.pack(pady=(0,10))

        # Dwell time between steps
        self.dwell_label = ctk.CTkLabel(self.amf_frame, text="Dwell Time (s):")
        self.dwell_label.pack()
        self.dwell_entry = ctk.CTkEntry(self.amf_frame, width=100)
        self.dwell_entry.insert(0, "1e-3")  # default 
        self.dwell_entry.pack(pady=(0,10))

        # Button to start the “experiment”
        self.run_button = ctk.CTkButton(
            self.amf_frame, text="Run AMF Experiment",
            command=self.run_amf_experiment
        )
        self.run_button.pack(pady=(10,0))

    def run_amf_experiment(self):
        """
        1) Reads user parameters c, T, N, direction, dwell time.
        2) For each time step, constructs a unitary, decomposes, applies phases, measures output power.
        3) Exports the results (time step vs. measured power on all outputs) to CSV.
        """
        try:
            c_val = float(self.c_entry.get())
            N_val = int(self.N_entry.get())
            dwell = float(self.dwell_entry.get())
            direction = self.direction_var.get()  

            rabi_cycles = float(self.rabi_entry.get())
            T_period = rabi_cycles * (math.pi / (2 * c_val))
            T_total = float(self.time_entry.get())  

        except ValueError as e:
            print(f"Error reading AMF inputs: {e}")
            return

        # Hamiltonians, 3x3
        H1 = np.array([[0,c_val,0], [c_val, 0, 0], [0, 0, 1]])
        H2 = np.array([[1, 0 ,0], [0,0,c_val], [0, c_val, 0]])
        H3 = np.array([[0,0,c_val], [0, 1, 0], [c_val, 0, 0]])

        # Initial conditions
        a = np.zeros(3)
        a[0] = 1 # first input
        a = a/np.linalg.norm(a)

        # Build a time array
        T_list = np.linspace(0, T_total, N_val)

        # Prepare to store data: e.g., a list of [t_step, power_ch0, power_ch1, ...]
        results = []
        channels = self.daq.list_ai_channels() or []  # make sure it's always a list

        for step_idx in range(N_val):
            current_time = T_list[step_idx]

            # Build the time-evolving unitary for this step
            U_step = self._build_unitary_at_timestep(
                current_time=current_time,
                H1=H1, H2=H2, H3=H3, 
                T_period=T_period,  
                direction=direction
            )

            #Decompose the unitary:
            try:
                # Perform decomposition
                I = itf.square_decomposition(U_step)
                bs_list = I.BS_list
                mzi_convention.clements_to_chip(bs_list)
        
                # Store the decomposition result in AppData
                setattr(AppData, 'default_json_grid', mzi_lut.get_json_output(self.n, bs_list))
        
            except Exception as e:
                print('Error in decomposition:', e)

            #Apply the phase:
            self.apply_phase_new()

            # Settle time for the system to reach steady state
            time.sleep(dwell)

            # Measure the output power with DAQ
            if channels:
                measured_values = self.daq.read_power_in_mW(channels=channels, samples_per_channel=5)
            else:
                measured_values = []

            if isinstance(measured_values, float):
                measured_values = [measured_values]

            results.append([step_idx + 1] + measured_values)

            # Export the results to CSV
        zero_config = self._create_zero_config()
        apply_grid_mapping(self.qontrol, zero_config, self.grid_size)

        self._export_results_to_csv(results, channels)
        print("AMF experiment complete!")
        # Create a zero-value configuration for all crosspoints.



    def _build_unitary_at_timestep(self, current_time, H1, H2, H3, T_period, direction):
        """
        Builds the time-evolving unitary at 'current_time' in [0..T_val], 
        using H1, H2, H3. Splits the total evolution into 3 segments: 
        H1->H2->H3 for CW or reversed for CCW.
        Then 3×3 is placed in top-left of NxN identity matrix.
        """

        def mod_with_quotient(x, mod):
            quotient = int(x // mod)
            remainder = x % mod
            return quotient, remainder

        q, r = mod_with_quotient(current_time, T_period)
        T_seg = T_period /3
        
        # Segment order
        if direction == "CW":
            H_seq = [H1, H2, H3]
        else:  # CCW
            H_seq = [H3, H2, H1]

        # Build full-cycle unitary
        U_cycle = expm(-1j * T_seg * H_seq[2]) @ expm(-1j * T_seg * H_seq[1]) @ expm(-1j * T_seg * H_seq[0])

        # Compute full cycle evolution [U_cycle]^q
        U = np.linalg.matrix_power(U_cycle, q)

        # Apply the remainder (partial segment)
        if r > 0:
            rem_U = np.eye(3, dtype=complex)
            for i in range(3):
                if r >= T_seg:
                    rem_U = expm(-1j * T_seg * H_seq[i]) @ rem_U
                    r -= T_seg
                elif r > 0:
                    rem_U = expm(-1j * r * H_seq[i]) @ rem_U
                    break
            U = rem_U @ U

        # Pad to NxN
        U_full = np.eye(self.n, dtype=complex)
        U_full[:3, :3] = U
        return U_full

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
        
        # Check if phase is within valid range
        if phase_value < c/np.pi:
            print(f"Warning: Phase {phase_value}π is less than offset phase {c/np.pi:.2f}π for channel {channel}")
            # Multiply phase_value by 2 and continue with calculation
            phase_value = phase_value + 2
            print(f"Using adjusted phase value: {phase_value}π")

        # Calculate heating power for this phase shift
        P = abs((phase_value*np.pi - c) / b)
        
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



    def _export_results_to_csv(self, results, channels):
        """Simple CSV exporter for time-step data."""
        if not results:
            print("No results to save.")
            return

        # Let user pick the export location
        path = filedialog.asksaveasfilename(
            title='Save AMF Results',
            defaultextension='.csv',
            filetypes=[('CSV files', '*.csv')]
        )
        if not path:
            return

        # Build header row: e.g. step, then channel names
        headers = ["time_step"] + channels

        try:
            with open(path, 'w', encoding='utf-8') as f:
                # Write header
                f.write(",".join(headers) + "\n")
                # Write rows
                for row in results:
                    # row = [step, v_ch0, v_ch1, ...]
                    line_str = ",".join(str(x) for x in row)
                    f.write(line_str + "\n")

            print(f"Results saved to {path}")
        except Exception as e:
            print(f"Failed to save results: {e}")







    def get_unitary_mapping(self):
        '''Returns a dictionary mapping tab names to their corresponding entry grids and AppData variables.'''
        return {
            'U1': (self.unitary_entries_U1, 'saved_unitary_U1'),
            'U2': (self.unitary_entries_U2, 'saved_unitary_U2'),
            'U3': (self.unitary_entries_U3, 'saved_unitary_U3'),
            }

    def get_active_tab(self):
        '''
        Returns the unitary entry grid (2D list) and corresponding AppData variable
        for the currently selected tab.
        '''
        return self.get_unitary_mapping().get(self.tabview.get(), (None, None))
        
    def get_unitary_by_tab(self, tab_name):
        '''
        Returns the unitary entry grid (2D list) and corresponding AppData variable
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
    
            # Recreate the grid and update reference
            new_entries = self.create_nxn_entries(container)
            setattr(self, f'unitary_entries_{tab_name}', new_entries)
    
            # Restore saved matrix or default to identity
            unitary_matrix = getattr(AppData, appdata_var, None)
            if unitary_matrix is None or unitary_matrix.shape != (self.n, self.n):
                unitary_matrix = np.eye(self.n, dtype=complex)
    
            self.fill_tab_entries(new_entries, unitary_matrix)
            setattr(AppData, appdata_var, unitary_matrix)