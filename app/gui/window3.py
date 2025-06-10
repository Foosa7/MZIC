# app/gui/window3.py

from app.imports import *
import tkinter.filedialog as filedialog
import math
import copy
from app.utils.qontrol.qmapper8x8 import create_label_mapping, apply_grid_mapping
from app.utils.unitary import mzi_lut
from app.utils.unitary import mzi_convention
from app.utils.appdata import AppData
from datetime import datetime
import re
from pnn.methods import decompose_clements, reconstruct_clements

class Window3Content(ctk.CTkFrame):

    def toggle_interpolation(self):
        """Toggle the global pnn_choose parameter in mzi_lut."""
        mzi_lut.pnn_choose = 1 if self.interp_var.get() else 0
        print(f"Interpolation {'enabled' if mzi_lut.pnn_choose else 'disabled'} (pnn_choose={mzi_lut.pnn_choose})")
    
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

        # Create button frame using pack
        button_frame = ctk.CTkFrame(self.bottom_buttons_frame, fg_color='transparent')
        button_frame.pack(anchor='center', pady=(5,5))

        # Add the NH Experiment button using pack
        self.nh_button = ctk.CTkButton(
            button_frame,
            text="Run NH Experiment",
            command=self.run_nh_experiment_from_folder,
            width=120,
            height=30
        )
        self.nh_button.pack(side='left', padx=5, pady=5)


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


        # Interpolation toggle
        self.interp_var = ctk.BooleanVar(value=bool(mzi_lut.pnn_choose))
        self.interp_checkbox = ctk.CTkCheckBox(
            self.bottom_buttons_frame,
            text="Interpolation",
            variable=self.interp_var,
            command=self.toggle_interpolation
        )
        self.interp_checkbox.pack(anchor='center', pady=(5, 5))

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
        H1 = np.array([[0,     c_val, 0    ],
                       [c_val, 0,     0    ],
                       [0,     0,     0    ]], dtype=float)
        H2 = np.array([[0,     0,     0    ],
                       [0,     0,     c_val],
                       [0,     c_val, 0    ]], dtype=float)
        H3 = np.array([[0,     0,     c_val],
                       [0,     0,     0    ],
                       [c_val, 0,     0    ]], dtype=float)

        # Initial conditions
        a = np.zeros(3)
        a[0] = 1 # first input
        a = a/np.linalg.norm(a)

        # Build a time array
        T_list = np.linspace(0, T_total, N_val)

        # Prepare to store data: e.g., a list of [t_step, power_ch0, power_ch1, ...]
        results = []

        # headers = ["time_step", "site1", "site2", "site3"]
        headers = ["timestamp", "time_step", "site1", "site2", "site3"] # Updated headers


        for step_idx in range(N_val):
            current_time = T_list[step_idx]

            # Build the time-evolving unitary for this step
            U_step = self._build_unitary_at_timestep(
                current_time=current_time,
                H1=H1, H2=H2, H3=H3, 
                T_period=T_period,  
                direction=direction
            )
            
            '''
            # Save unitary at each timestep
            unitary_dir = "unitary_history"
            os.makedirs(unitary_dir, exist_ok=True)
            unitary_path = os.path.join(unitary_dir, f"unitary_step_{step_idx+1:03d}.npy")
            np.save(unitary_path, U_step)
            '''

            #Decompose the unitary:
            try:
                # Perform decomposition
                I = itf.square_decomposition(U_step)
                bs_list = I.BS_list
                print(bs_list)
                mzi_convention.clements_to_chip(bs_list)
        
                # Store the decomposition result in AppData
                setattr(AppData, 'default_json_grid', mzi_lut.get_json_output(self.n, bs_list))
        
            except Exception as e:
                print('Error in decomposition:', e)

            #Apply the phase:
            self.apply_phase_new()

            # Settle time for the system to reach steady state
            time.sleep(dwell)

            # Read DAQ channels and get values
            daq_values = [0.0, 0.0, 0.0]  # Default values
            if self.daq and self.daq.list_ai_channels():
                channels = ["Dev1/ai0", "Dev1/ai1"]
                try:
                    self._read_all_daq_channels()
                    # Get the values from the last reading
                    if hasattr(self, '_daq_last_result'):
                        lines = self._daq_last_result.split('\n')
                        # Parse the power values from each line
                        # Format is like "Dev1/ai0 -> X.XXX uW"
                        daq_values = []
                        for line in lines:
                            if '->' in line:
                                value = float(line.split('->')[1].split()[0])
                                daq_values.append(value)
                    
                    # Ensure we have at least 3 values (pad with 0 if needed)
                    while len(daq_values) < 3:
                        daq_values.append(0.0)
                        
                    # Clear DAQ task after reading
                    self.daq.clear_task()
                except Exception as e:
                    print(f"Error reading DAQ: {e}")
                    daq_values = [0.0, 0.0, 0.0]

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
            
            current_timestamp = datetime.now().strftime("%H:%M:%S")
            # Build one row => [step_idx+1, site1, site2, site3]
            row = [current_timestamp, step_idx + 1, daq_values[0], daq_values[1], daq_values[2]]
            results.append(row)

            # # Create a zero-value configuration for all crosspoints.
            # zero_config = self._create_zero_config()
            
            # # Apply the zero configuration to the device.
            # apply_grid_mapping(self.qontrol, zero_config, self.grid_size)
            # print("All values set to zero")
            # time.sleep(dwell/2)

            print('Step: ', step_idx + 1)

        self._export_results_to_csv(results, headers)
        print("AMF experiment complete!")
        # Create a zero-value configuration for all crosspoints.


    def run_nh_experiment_from_folder(self):
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

            # Get .npy files with expected naming pattern
            # npy_files = sorted(
            #     # [f for f in os.listdir(folder_path) if f.endswith(".npy") and f.startswith("unitary_step_")],
            #     [f for f in os.listdir(folder_path) if f.endswith(".npy") and f.startswith("step_")],                
            #     key=lambda x: int(x.split("_")[2].split(".")[0])  # Extract number from 'unitary_step_001.npy'
            # )
            # Get .npy files with expected naming pattern
            
            
            '''
            npy_files = sorted(
                [f for f in os.listdir(folder_path) if f.endswith(".npy") and f.startswith("step_")],
                key=lambda x: int(x.split("_")[0].split(".")[0])  # Extract number from 'step_1.npy'
            )
            if not npy_files:
                print("No unitary step files found in selected folder.")
                return

            '''

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


                    '''
                    I = itf.square_decomposition(U_step)
                    bs_list = I.BS_list
                    mzi_convention.clements_to_chip(bs_list)
                    setattr(AppData, 'default_json_grid', mzi_lut.get_json_output(self.n, bs_list))
                    '''

                    [A_phi, A_theta, *_] = decompose_clements(U_step, block='mzi')
                    
                    # COMMON MODE PHASE
    
                    # ROW 1
                    A_phi[0][0] = A_phi[0][0] 
                    A_phi[0][1] = A_phi[0][1] + A_theta[1][0] + np.pi / 2
                    A_phi[0][2] = A_phi[0][2] + A_theta[1][1] + np.pi / 2
                    A_phi[0][3] = A_phi[0][2] + A_theta[1][2] + np.pi / 2
                    
                    
                    # ROW 2
                    A_phi[1][0] = A_phi[1][0] - A_theta[0][0] + A_theta[2][0]
                    A_phi[1][1] = A_phi[1][1] - A_theta[0][1] + A_theta[2][1]
                    A_phi[1][2] = A_phi[1][2] - A_theta[0][2] + A_theta[2][2]
                    A_phi[1][3] = A_phi[1][3] - A_theta[0][3] + A_theta[2][3]
                    
                    
                    # ROW 3
                    A_phi[2][0] = A_phi[2][0] 
                    A_phi[2][1] = A_phi[2][1] - A_theta[1][0] + A_theta[3][0]
                    A_phi[2][2] = A_phi[2][2] - A_theta[1][1] + A_theta[3][1]
                    A_phi[2][3] = A_phi[2][3] - A_theta[1][2] + A_theta[3][2]
                    
                    
                    # ROW 4
                    A_phi[3][0] = A_phi[3][0] - A_theta[2][0] + A_theta[4][0]
                    A_phi[3][1] = A_phi[3][1] - A_theta[2][1] + A_theta[4][1]
                    A_phi[3][2] = A_phi[3][2] - A_theta[2][2] + A_theta[4][2]
                    A_phi[3][3] = A_phi[3][3] - A_theta[2][3] + A_theta[4][3]
                    
                    
                    # ROW 5
                    A_phi[4][0] = A_phi[4][0] 
                    A_phi[4][1] = A_phi[4][1] - A_theta[3][0] + A_theta[5][0]
                    A_phi[4][2] = A_phi[4][2] - A_theta[3][1] + A_theta[5][1]
                    A_phi[4][3] = A_phi[4][3] - A_theta[3][2] + A_theta[5][2]
                    
                    
                    # ROW 6
                    A_phi[5][0] = A_phi[5][0] - A_theta[4][0] + A_theta[6][0]
                    A_phi[5][1] = A_phi[5][1] - A_theta[4][1] + A_theta[6][1]
                    A_phi[5][2] = A_phi[5][2] - A_theta[4][2] + A_theta[6][2]
                    A_phi[5][3] = A_phi[5][3] - A_theta[4][3] + A_theta[6][3]
                    
                    
                    # ROW 7
                    A_phi[6][0] = A_phi[6][0] 
                    A_phi[6][1] = A_phi[6][1] - A_theta[5][0] - np.pi / 2
                    A_phi[6][2] = A_phi[6][2] - A_theta[5][1] - np.pi / 2
                    A_phi[6][3] = A_phi[6][3] - A_theta[5][2] - np.pi / 2
                    
                    A_theta *= 2/np.pi

                    #A_phi += np.pi
                    A_phi = A_phi % (2*np.pi)
                    A_phi /= np.pi
                    
                    setattr(AppData, 'default_json_grid', mzi_lut.get_json_output(self.n, A_theta, A_phi))

                except Exception as e:
                    print(f"Error in decomposition: {e}")
                    continue

                # Apply phases
                self.apply_phase_new()

                # DAQ measurements with continuous sampling during dwell time
                daq_values = [0.0, 0.0, 0.0, 0.0]
                if self.daq and self.daq.list_ai_channels():
                    channels = ["Dev1/ai0", "Dev1/ai1", "Dev1/ai2", "Dev1/ai3"]
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
                print("\nNH experiment complete!")
                
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


    # def run_nh_experiment_from_folder(self):
    #     """
    #     1) Prompts the user to select a folder containing .npy files.
    #     2) Loads each .npy file in sequence, assigns it to U_step, and processes it.
    #     3) Applies phases, measures output power, and saves results to a CSV file.
    #     """
    #     try:
    #         # Get dwell time
    #         dwell = float(self.dwell_entry.get())
    #     except ValueError as e:
    #         print(f"Error reading NH inputs: {e}")
    #         return

    #     # Prompt the user to select a folder
    #     folder_path = filedialog.askdirectory(title="Select Folder Containing .npy Files")
    #     if not folder_path:
    #         print("No folder selected. Aborting.")
    #         return

    #     # # Get all .npy files in the folder, sorted by step number
    #     # npy_files = sorted(
    #     #     [f for f in os.listdir(folder_path) if f.endswith(".npy")],
    #     #     key=lambda x: int(x.split("_")[1].split(".")[0])  # Extract step number from filename
    #     # )

    #     # Get all .npy files in the folder, sorted by step number
    #     npy_files = sorted(
    #         [f for f in os.listdir(folder_path) if f.endswith(".npy") and f.startswith("unitary_step_")],
    #         key=lambda x: int(x.split("_")[2].split(".")[0])  # Extract number from 'unitary_step_001.npy'
    #     )

    #     if not npy_files:
    #         print("No .npy files found in the selected folder.")
    #         return

    #     # Prepare to store data: e.g., a list of [step_idx, power_ch0, power_ch1]
    #     results = []
    #     # headers = ["step", "site1", "site2"]
    #     headers = ["timestamp", "step", "site1", "site2"] # Updated headers

    #     for step_idx, npy_file in enumerate(npy_files, start=1):
    #         file_path = os.path.join(folder_path, npy_file)

    #         # Load the .npy file as U_step
    #         try:
    #             U_step = np.load(file_path)
    #             print(f"Loaded {npy_file}")
    #         except Exception as e:
    #             print(f"Error loading {npy_file}: {e}")
    #             continue

    #         # Decompose the unitary
    #         try:
    #             I = itf.square_decomposition(U_step)
    #             bs_list = I.BS_list
    #             print(bs_list)
    #             mzi_convention.clements_to_chip(bs_list)

    #             # Store the decomposition result in AppData
    #             setattr(AppData, 'default_json_grid', mzi_lut.get_json_output(self.n, bs_list))
    #         except Exception as e:
    #             print(f"Error in decomposition for {npy_file}: {e}")
    #             continue

    #         # Apply the phase
    #         self.apply_phase_new()

    #         # Settle time for the system to reach steady state
    #         time.sleep(dwell)

    #         # ---- DAQ measurements (ai0, ai1 => site1, site2) ----
    #         daq_values = [0.0, 0.0]
    #         if self.daq and self.daq.list_ai_channels():
    #             channels = ["Dev1/ai0", "Dev1/ai1"]
    #             daq_vals = self.daq.read_power(channels=channels, samples_per_channel=1, unit='uW')
    #             if isinstance(daq_vals, list) and len(daq_vals) >= 2:  # If daq_vals has 2 values, store them
    #                 daq_values = [daq_vals[0], daq_vals[1]]
            
    #         current_timestamp = datetime.now().strftime("%H:%M:%S")
    #         # Build one row => [step_idx, site1_daq, site2_daq]
    #         row = [current_timestamp, step_idx, daq_values[0], daq_values[1]]
    #         results.append(row)


    #     # Export the results to CSV
    #     self._export_results_to_csv(results, headers)
    #     print("NH complete!")      
    #             # Create a zero-value configuration for all crosspoints.
    #     zero_config = self._create_zero_config()

    #     # Apply the zero configuration to the device.
    #     apply_grid_mapping(self.qontrol, zero_config, self.grid_size)
    #     print("All values set to zero")

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

        # --- calibration parameters -------------------------------------------
        A = params['amp']
        b = params['omega']            
        c = params['phase']            # offset phase at I = 0  
        d = params['offset']           # amplitude offset

        # --- minimal phase advance --------------------------------------------
        phase_target = phase_value * np.pi          # requested phase   [rad]
        delta_phase  = (phase_target - c) % (2*np.pi) # 0 ≤ δφ < 2π

        # Heater power
        P = delta_phase / b     # always ≥ 0

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

    def _export_results_to_csv(self, results, headers):
        """Export step data with custom headers (includes DAQ + Thorlabs)."""
        if not results:
            print("No results to save.")
            return

        path = filedialog.asksaveasfilename(
            title='Save AMF Results',
            defaultextension='.csv',
            filetypes=[('CSV files', '*.csv')]
        )
        if not path:
            return

        try:
            with open(path, 'w', encoding='utf-8') as f:
                # Write header
                f.write(",".join(headers) + "\n")
                # Write rows
                for row in results:
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
            
            '''
            # Perform decomposition
            I = itf.square_decomposition(matrix_u)
            bs_list = I.BS_list
            mzi_convention.clements_to_chip(bs_list)
    
            # Store the decomposition result in AppData
            setattr(AppData, 'default_json_grid', mzi_lut.get_json_output(self.n, bs_list))
            '''

            [A_phi, A_theta, *_] = decompose_clements(matrix_u, block='mzi')
            A_theta *= 2/np.pi
            A_phi += np.pi
            A_phi = A_phi % (2*np.pi)
            A_phi /= np.pi
            
            setattr(AppData, 'default_json_grid', mzi_lut.get_json_output(self.n, A_theta, A_phi))
            
            
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