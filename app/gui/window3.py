# app/gui/window3.py

from app.imports import *
import tkinter.filedialog as filedialog
import copy
import sympy as sp
from app.utils.qontrol.qmapper8x8 import create_label_mapping, apply_grid_mapping
from app.utils.qontrol.mapping_utils import get_mapping_functions
from app.utils.appdata import AppData
from app.utils.switch_measurements import SwitchMeasurements
from app.utils.decomposition import (
    decomposition, 
    decompose_clements,
    clements_to_chip,
    get_json_interferometer,
    get_json_pnn
)

class Window3Content(ctk.CTkFrame):
    
    def __init__(self, master, app, qontrol, thorlabs, daq, switch, switch_input, switch_output, grid_size = "12x12", **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        self.qontrol = qontrol
        self.thorlabs = thorlabs
        self.daq = daq
        self.switch = switch #Backward compatibility (output switch)
        self.switch_input = switch_input
        self.switch_output = switch_output
        
        # NxN dimension
        self.n = int(grid_size.split('x')[0])
        self.grid_size = grid_size 

        # Main layout
        self.content_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.content_frame.pack(expand=True, fill='both', padx=2, pady=2)

        # Configure grid columns - left for controls, right for status
        self.content_frame.grid_columnconfigure(0, weight=1)  # Left column (controls, plots)
        self.content_frame.grid_columnconfigure(1, weight=2)  # Right column (status)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Left side container
        self.left_frame = ctk.CTkFrame(self.content_frame, fg_color='transparent')
        self.left_frame.grid(row=0, column=0, sticky='nsew', padx=(5,2), pady=5)

        # Right side container 
        self.right_container = ctk.CTkFrame(self.content_frame, fg_color='transparent')
        self.right_container.grid(row=0, column=1, sticky='nsew', padx=(2,5), pady=5)

        # ──────────────────────────────────────────────────────────────
        # 1) UNITARY-MATRIX TOOLS
        # ──────────────────────────────────────────────────────────────
        self.unitary_buttons_frame = ctk.CTkFrame(
            self.left_frame, fg_color="transparent"
        )
        self.unitary_buttons_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # main action buttons
        self.apply_unitary_button = ctk.CTkButton(
            self.unitary_buttons_frame, text="Decompose",
            command=self.decompose_unitary
        )
        self.apply_unitary_button.pack(anchor="center", pady=(5, 5))


        # ──────────────────────────────────────────────────────────────
        # 2) EXPERIMENT CONTROLS  
        # ──────────────────────────────────────────────────────────────
        self.cycle_frame = ctk.CTkFrame(
            self.left_frame, fg_color="#2B2B2B", corner_radius=8
        )
        self.cycle_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.cycle_frame.grid_columnconfigure(1, weight=1)

        # title row
        ctk.CTkLabel(
            self.cycle_frame, text="⚙  Experiment Controls",
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(8, 6))

        # ─────────────────────  row – Cycle button
        self.cycle_unitaries_button = ctk.CTkButton(
            self.cycle_frame, text="Cycle Unitaries",
            command=self.cycle_unitaries, width=140, height=32
        )
        self.cycle_unitaries_button.grid(row=1, column=0, padx=10, pady=4, sticky="w")
        
        # Interpolation toggle 
        self.interpolation_var = ctk.BooleanVar(value=getattr(AppData, "interpolation_enabled", False))
        self.interpolation_checkbox = ctk.CTkCheckBox(
            self.cycle_frame,
            text="Interpolation",
            variable=self.interpolation_var,
            command=self._on_interpolation_toggle
        )
        self.interpolation_checkbox.grid(row=1, column=2, columnspan=2,  padx=(10, 0), pady=4)
        # ─────────────────────  row – dwell-time (ms)
        ctk.CTkLabel(self.cycle_frame, text="Dwell Time (ms):")\
            .grid(row=2, column=0, sticky="e", padx=10, pady=4)

        dwell_time_frame = ctk.CTkFrame(self.cycle_frame, fg_color="transparent")
        dwell_time_frame.grid(row=2, column=1, sticky="ew", padx=10, pady=4)
        dwell_time_frame.grid_columnconfigure(0, weight=1)

        # shared state
        #self.dwell_var = ctk.StringVar(value="500")   # milliseconds
        self.dwell_var = ctk.StringVar(value=getattr(AppData, "dwell_time", "500"))
        _SLIDER_MIN_MS = 1
        _SLIDER_MAX_MS = 5_000
        self._dwell_lock = False                      # recursion guard

        def _slider_moved(value_ms: float):
            if self._dwell_lock:
                return
            self._dwell_lock = True
            self.dwell_var.set(f"{int(value_ms)}")    # keep as ms
            self._dwell_lock = False
            AppData.dwell_time = self.dwell_var.get()  # Save to AppData

        def _entry_changed(*_):
            if self._dwell_lock:
                return
            try:
                ms = int(float(self.dwell_var.get()))
                ms = max(_SLIDER_MIN_MS, min(_SLIDER_MAX_MS, ms))
                self._dwell_lock = True
                self.dwell_slider.set(ms)
                self._dwell_lock = False
            except ValueError:
                # ignore incomplete/invalid input
                pass

        self.dwell_var.trace_add("write", _entry_changed)

        # slider: 1 ms → 5 000 ms
        self.dwell_slider = ctk.CTkSlider(
            dwell_time_frame,
            from_=_SLIDER_MIN_MS,
            to=_SLIDER_MAX_MS,
            number_of_steps=_SLIDER_MAX_MS - _SLIDER_MIN_MS,
            command=_slider_moved,
        )
        self.dwell_slider.set(1e2)                  # default 100 ms
        self.dwell_slider.grid(row=0, column=0, sticky="ew")

        # entry bound to the same StringVar
        self.dwell_entry = ctk.CTkEntry(
            dwell_time_frame, width=70, textvariable=self.dwell_var
        )
        self.dwell_entry.grid(row=0, column=1, padx=(8, 0))

        """
        Remember to convert ms to seconds for experiment later
        dwell_ms = float(self.dwell_entry.get())
        dwell_seconds = dwell_ms / 1000.0
        """

        # Adjust column configuration for proper alignment
        self.cycle_frame.grid_columnconfigure(0, weight=1)
        self.cycle_frame.grid_columnconfigure(1, weight=1)

        # ─────────────────────  row 3 – measurement source
        #self.measurement_source = ctk.StringVar(value="Thorlabs")
        self.measurement_source = ctk.StringVar(value=getattr(AppData, "measurement_source", "Thorlabs"))
        def _measurement_source_changed(*args):
            AppData.measurement_source = self.measurement_source.get()
        self.measurement_source.trace_add("write", _measurement_source_changed)
        
        ctk.CTkLabel(self.cycle_frame, text="Measurement source:")\
            .grid(row=3, column=0, sticky="e", padx=10, pady=4)

        measure_frame = ctk.CTkFrame(self.cycle_frame, fg_color="transparent")
        measure_frame.grid(row=3, column=1, sticky="w", padx=10, pady=4)

        ctk.CTkRadioButton(measure_frame, text="DAQ",
            variable=self.measurement_source, value="DAQ").pack(side="left", padx=3)
        ctk.CTkRadioButton(measure_frame, text="Thorlabs",
            variable=self.measurement_source, value="Thorlabs").pack(side="left", padx=3)

        # ─────────────────────  row 4 – Package option
        ctk.CTkLabel(self.cycle_frame, text="Package:").grid(row=4, column=0, sticky="e", padx=10, pady=4)
        #self.decomposition_package_var = ctk.StringVar(value="pnn")  # Default value
        self.decomposition_package_var = ctk.StringVar(
            value=getattr(AppData, "decomposition_package", "pnn")
        )
        self.decomposition_package_dropdown = ctk.CTkOptionMenu(
            self.cycle_frame,
            variable=self.decomposition_package_var,
            values=["interferometer", "pnn"]
        )
        self.decomposition_package_dropdown.grid(row=4, column=1, sticky="ew", padx=10, pady=4)
        def on_package_changed(*args):
            AppData.decomposition_package = self.decomposition_package_var.get()
        self.decomposition_package_var.trace_add("write", on_package_changed)
        # ─────────────────────  row 5 – Global Phase option
        ctk.CTkLabel(self.cycle_frame, text="Global Phase:").grid(row=5, column=0, sticky="e", padx=10, pady=4)
        #self.global_phase_var = ctk.BooleanVar(value=False)  # Default: disabled
        
        self.global_phase_var = ctk.BooleanVar(value=getattr(AppData, "global_phase", False))
        def on_global_phase_changed(*args):
            AppData.global_phase = self.global_phase_var.get()
        self.global_phase_var.trace_add("write", on_global_phase_changed)
        
        self.global_phase_checkbox = ctk.CTkCheckBox(
            self.cycle_frame,
            text="Enable",
            variable=self.global_phase_var
        )
        self.global_phase_checkbox.grid(row=5, column=1, sticky="w", padx=10, pady=4)

        # ─────────────────────  row 6 – Measure using switch
        ctk.CTkLabel(self.cycle_frame, text="Measure using switch:")\
            .grid(row=6, column=0, sticky="e", padx=10, pady=4)

        #self.measure_switch_var = ctk.StringVar(value="No")
        self.measure_switch_var = ctk.StringVar(value=getattr(AppData, "measure_switch", "No"))
        def on_measure_switch_changed_var(*args):
            AppData.measure_switch = self.measure_switch_var.get()
        self.measure_switch_var.trace_add("write", on_measure_switch_changed_var)
        
        self.measure_switch_menu = ctk.CTkOptionMenu(
            self.cycle_frame,
            variable=self.measure_switch_var,
            values=["Yes", "No"],
            command=self._on_measure_switch_changed
        )
        self.measure_switch_menu.grid(row=6, column=1, sticky="w", padx=10, pady=4)

        # ─────────────────────  row 7 – Switch channels (initially hidden)
        self.switch_channels_label = ctk.CTkLabel(
            self.cycle_frame, 
            text="Switch channels:"
        )
        self.switch_channels_label.grid(row=7, column=0, sticky="e", padx=10, pady=4)

        self.switch_channels_entry = ctk.CTkEntry(
            self.cycle_frame,
            placeholder_text="e.g., 1,2,3,4 or 1-8"
        )
        self.switch_channels_entry.insert(0, "1,2,3")  # Default
        self.switch_channels_entry.grid(row=7, column=1, sticky="ew", padx=10, pady=4)

        # Initially hide the channel selection
        self.switch_channels_label.grid_remove()
        self.switch_channels_entry.grid_remove()

        # ──────────────────────────────────────────────────────────────
        # 3) STATUS DISPLAY
        # ──────────────────────────────────────────────────────────────
        self.status_frame = ctk.CTkFrame(
            self.right_container, fg_color="#1E1E1E", corner_radius=8
        )
        self.status_frame.pack(fill="both", expand=True, padx=(0, 10), pady=(10, 50))

        # Title
        ctk.CTkLabel(
            self.status_frame, text="📊 Experiment Status",
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", padx=10, pady=(8, 4))
        
        # Status text display
        self.status_textbox = ctk.CTkTextbox(
            self.status_frame,
            height=150,
            font=("Consolas", 10),
            fg_color="#2B2B2B"
        )
        self.status_textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Configure text tags for colored output
        self.status_textbox.tag_config("header", foreground="#4A9EFF")
        self.status_textbox.tag_config("success", foreground="#4CAF50")
        self.status_textbox.tag_config("error", foreground="#FF5252")
        self.status_textbox.tag_config("warning", foreground="#FFA726")
        self.status_textbox.tag_config("info", foreground="#E0E0E0")
        
        # Simple text progress bar
        self.progress_label = ctk.CTkLabel(
            self.status_frame,
            text="Progress: [░░░░░░░░░░] 0/0 (0%)",
            font=("Consolas", 12),
            anchor="w",
            text_color="#4CAF50"  
        )
        self.progress_label.pack(fill="x", padx=10, pady=(0, 10))
        
        # Current measurement display
        self.measurement_frame = ctk.CTkFrame(
            self.status_frame,
            fg_color="#363636",
            corner_radius=6
        )
        self.measurement_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.measurement_label = ctk.CTkLabel(
            self.measurement_frame,
            text="Latest Measurements: Waiting to start...",
            font=("Segoe UI", 11),
            anchor="w"
        )
        self.measurement_label.pack(fill="x", padx=10, pady=8)

        # ──────────────────────────────────────────────────────────────
        # Load any saved unitary into the entry grid
        # ──────────────────────────────────────────────────────────────

        # Add a text box to display the matrix
        self.unitary_textbox = ctk.CTkTextbox(
            self.left_frame, width=900, height=140, wrap="none"
        )
        self.unitary_textbox.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        # 从 AppData 中加载记忆的内容
        if getattr(AppData, "unitary_textbox_content", None):
            self.unitary_textbox.insert("1.0", AppData.unitary_textbox_content)
    
    # def _on_interpolation_toggle(self):
    #     AppData.interpolation_enabled = self.interpolation_var.get()
    #     if AppData.interpolation_enabled:
    #         if AppData.interpolated_theta:
    #             # If interpolation is already done, just update the status
    #             self.update_status("Interpolation already performed. Using cached values.", "info")
    #             return


    #         # Only 6 special nodes are interpolated
    #         special_nodes = ["E1", "F1", "G1", "H1", "E2", "G2"]
    #         from tests.interpolation.data import Reader_interpolation as reader
    #         interpolated = {}
    #         # 读取当前 AppData.default_json_grid
    #         json_grid = AppData.default_json_grid
    #         for node in special_nodes:
    #             try:
    #                 # 读取原始theta
    #                 theta_val = float(json_grid[node]['theta'])
    #                 reader.load_sweep_file(f"{node}_theta_200_steps.csv")
    #                 interpolated_theta = reader.theta_trans(theta_val * np.pi, reader.theta, reader.theta_corrected)/np.pi
    #                 interpolated[node] = interpolated_theta
    #                 # 直接修改 AppData.default_json_grid 里的 theta
    #                 json_grid[node]['theta'] = str(interpolated_theta)
    #             except Exception as e:
    #                 print(f"Interpolation failed for {node}: {e}")
    #         AppData.interpolated_theta = interpolated
    #     else:
    #         AppData.interpolated_theta = {}

    def _on_interpolation_toggle(self):
        AppData.interpolation_enabled = self.interpolation_var.get()
        if AppData.interpolation_enabled:
            if AppData.interpolated_theta:
                # 如果已经插值过，直接返回
                return

            # 只对6个special nodes做插值
            special_nodes = ["E1", "F1", "G1", "H1", "E2", "G2"]
            from tests.interpolation.data import Reader_interpolation as reader
            interpolated = {}
            # 读取当前 AppData.default_json_grid
            json_grid = AppData.default_json_grid
            for node in special_nodes:
                try:
                    # 读取原始theta
                    theta_val = float(json_grid[node]['theta'])
                    reader.load_sweep_file(f"{node}_theta_200_steps.csv")
                    interpolated_theta = reader.theta_trans(theta_val * np.pi, reader.theta, reader.theta_corrected) / np.pi
                    interpolated[node] = interpolated_theta
                    # 直接修改 AppData.default_json_grid 里的 theta
                    json_grid[node]['theta'] = str(interpolated_theta)
                except Exception as e:
                    logging.error(f"Interpolation failed for {node}: {e}")
            AppData.interpolated_theta = interpolated
        else:
            # 如果禁用 Interpolation，重新基于 unitary_textbox 的矩阵分解更新 JSON
            try:
                # 从 unitary_textbox 中读取矩阵
                matrix_u = self._read_matrix_from_textbox()
                # 根据当前 package 选择分解方法
                package = self.decomposition_package_var.get()
                if package == "pnn":
                    #from pnn.methods import decompose_clements
                    #### Shall we use mzi or bs in this pnn package?
                    [A_phi, A_theta, *_] = decompose_clements(matrix_u, block='mzi')
                    A_theta *= 2 / np.pi
                    #A_phi += np.pi
                    #A_phi = A_phi % (2 * np.pi)
                    A_phi /= np.pi
                    json_output = get_json_pnn(self.n, A_theta, A_phi)
                elif package == "interferometer":
                    I = decomposition(matrix_u, global_phase=self.global_phase_var.get())
                    bs_list = I.BS_list
                    clements_to_chip(bs_list)
                    json_output = get_json_interferometer(self.n, bs_list)
                # 更新 AppData.default_json_grid
                AppData.default_json_grid = json_output
            except Exception as e:
                logging.error(f"Failed to reset JSON grid after disabling interpolation: {e}")
            AppData.interpolated_theta = {}
    
    def _read_matrix_from_textbox(self) -> np.ndarray:
        """Read the matrix from the unitary_textbox."""
        try:
            content = self.unitary_textbox.get("1.0", "end").strip()
            rows = content.split("\n")
            matrix = []
            for row in rows:
                elements = row.split()
                matrix.append([complex(elem.replace("j", "j")) for elem in elements])
            return np.array(matrix, dtype=complex)
        except Exception as e:
            logging.error(f"Failed to read matrix from textbox: {e}")
            return np.eye(self.n, dtype=complex)  # Return identity matrix as fallback
    
    def update_status(self, message, tag="info"):
        """Update the status display with a new message"""
        # Check if we're currently at the bottom before inserting
        current_position = self.status_textbox.yview()[1]  # Get bottom position of view
        was_at_bottom = current_position >= 0.99  # Check if we're near the bottom
        
        # Insert the new message
        self.status_textbox.insert("end", f"{message}\n", tag)
        
        # Only auto-scroll if we were already at the bottom
        if was_at_bottom:
            self.status_textbox.see("end")
        
        self.update()
        
    def clear_status(self):
        """Clear the status display"""
        self.status_textbox.delete("1.0", "end")
        
    def update_progress(self, current, total):
        """Update the progress bar with arrow style"""
        if total > 0:
            # Calculate progress
            percentage = int((current / total) * 100)
            bar_width = 20  # Total width of the progress bar
            filled_width = int((current / total) * bar_width)
            
            # Create the arrow-style progress bar
            if filled_width == 0:
                # No progress yet
                bar = " " * bar_width
            elif filled_width >= bar_width:
                # Complete
                bar = "=" * bar_width
            else:
                # In progress - show arrow
                bar = "=" * (filled_width - 1) + ">" + " " * (bar_width - filled_width)
            
            # Update label
            progress_text = f"Progress: [{bar}] {percentage}% ({current}/{total})"
            self.progress_label.configure(text=progress_text)
            self.update()
            
    def update_measurements(self, measurements, labels):
        """Update the measurement display with latest values"""
        if measurements and labels:
            # Format measurements with 3 decimal places
            formatted = []
            for label, value in zip(labels, measurements):
                formatted.append(f"{label}: {value:.3f} µW")
            
            # Show up to 4 measurements per line
            lines = []
            for i in range(0, len(formatted), 4):
                lines.append("  |  ".join(formatted[i:i+4]))
            
            display_text = "\n".join(lines)
            self.measurement_label.configure(text=f"Latest Measurements:\n{display_text}")
        else:
            self.measurement_label.configure(text="Latest Measurements: No data")
        self.update()

    # Method to handle switch option changes
    def _on_measure_switch_changed(self, value):
        """Show/hide switch channel selection based on measure option"""
        if value == "Yes":
            self.switch_channels_label.grid()
            self.switch_channels_entry.grid()
        else:
            self.switch_channels_label.grid_remove()
            self.switch_channels_entry.grid_remove()    

    ### cycle funtion
    def cycle_unitaries(self):
        """
        1) Ask for a folder with step_*.npy files.
        2) For each file:
            – decompose → apply phases
            – wait/measure for <dwell> ms
            – record power from the selected measurement source
        3) Save a CSV with measurements from either switch channels or devices directly
        """
        try:
            # Clear previous status and reset progress
            self.clear_status()
            self.progress_label.configure(text="Progress: [░░░░░░░░░░] 0/0 (0%)")  # Reset progress
            self.measurement_label.configure(text="Latest Measurements: Starting...")
            
            # Change button to show it's running
            self.cycle_unitaries_button.configure(text="Running...", state="disabled")
            self.update()
            
            # Log start
            self.update_status("🚀 Starting Unitary Cycling Experiment", "header")
            self.update_status(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "info")
            
            # ───────────────────────────────────────────────────────
            # 0.  Read user-selected parameters
            # ───────────────────────────────────────────────────────
            dwell_ms = float(self.dwell_entry.get())
            dwell_s  = dwell_ms / 1000.0
            sample_rate = 1_000
            samples_per_channel = int(dwell_s*sample_rate)

            use_source = self.measurement_source.get()
            use_global_phase = self.global_phase_var.get()
            use_switch = self.measure_switch_var.get() == "Yes"
            
            # Log configuration
            self.update_status(f"\n⚙️ Configuration:", "header")
            self.update_status(f"  • Dwell time: {dwell_ms} ms", "info")
            self.update_status(f"  • Measurement source: {use_source}", "info")
            self.update_status(f"  • Global phase: {'Enabled' if use_global_phase else 'Disabled'}", "info")
            self.update_status(f"  • Using switch: {'Yes' if use_switch else 'No'}", "info")

            # Get switch channels if using switch
            switch_channels = []
            measurement_labels = []  # For display
            
            if use_switch:
                if not self.switch:
                    raise ValueError("Switch device not available but 'Measure using switch' is selected")
                
                channel_string = self.switch_channels_entry.get()
                switch_channels = SwitchMeasurements.parse_switch_channels(channel_string)
                
                if not switch_channels:
                    raise ValueError("No valid switch channels specified")
                    
                self.update_status(f"  • Switch channels: {switch_channels}", "info")
                measurement_labels = [f"Ch{ch}" for ch in switch_channels]

            # Prepare headers based on measurement configuration
            headers = ["timestamp", "step"]
            
            if use_switch:
                headers.extend(SwitchMeasurements.create_headers_with_switch(switch_channels, "mW"))
                num_measurements = len(switch_channels)
            else:
                # Headers for direct device measurements
                if use_source == "DAQ":
                    if self.daq:
                        daq_channels = self.daq.list_ai_channels()
                        headers.extend([f"{ch}_mW" for ch in daq_channels])
                        num_measurements = len(daq_channels)
                        measurement_labels = daq_channels
                    else:
                        self.update_status("❌ No DAQ device available", "error")
                        return
                else:  # Thorlabs
                    if self.thorlabs:
                        if isinstance(self.thorlabs, list):
                            num_devices = len(self.thorlabs)
                        else:
                            num_devices = 1
                        headers.extend(SwitchMeasurements.create_headers_thorlabs(num_devices, "mW"))
                        num_measurements = num_devices
                        measurement_labels = [f"Thorlabs{i}" for i in range(num_devices)]
                    else:
                        self.update_status("❌ No Thorlabs device available", "error")
                        return

            # ───────────────────────────────────────────────────────
            # 1.  Location for the .npy step files
            # ───────────────────────────────────────────────────────
            self.update_status("\n📁 Select folder with unitary files...", "info")
            folder_path = filedialog.askdirectory(
                title="Select Folder Containing Unitary Step Files"
            )
            if not folder_path:
                self.update_status("❌ No folder selected. Aborting.", "error")
                self.cycle_unitaries_button.configure(text="Cycle Unitaries", state="normal")
                return

            # Use regex to extract numeric suffix from filenames
            npy_files = sorted(
                [f for f in os.listdir(folder_path) if f.endswith(".npy") and re.search(r"_(\d+)\.npy$", f)],
                key=lambda x: int(re.search(r"_(\d+)\.npy$", x).group(1))
            )

            if not npy_files:
                self.update_status("❌ No unitary step files found in selected folder.", "error")
                self.cycle_unitaries_button.configure(text="Cycle Unitaries", state="normal")
                return

            self.update_status(f"✅ Found {len(npy_files)} unitary files", "success")
            
            results = []
            total_steps = len(npy_files)

            # ───────────────────────────────────────────────────────
            # 2.  Iterate through every step_*.npy
            # ───────────────────────────────────────────────────────
            self.update_status(f"\n🔄 Processing {total_steps} steps...", "header")
            
            for step_idx, npy_file in enumerate(npy_files, start=1):
                file_path = os.path.join(folder_path, npy_file)

                # Current step status
                self.update_status(f"\n📍 Step {step_idx}/{total_steps}: {npy_file}", "info")

                # Update button to show progress
                self.cycle_unitaries_button.configure(text=f"Step {step_idx}/{total_steps}")
                self.update()

                try:
                    self.update_status("  • Loading and decomposing unitary...", "info")
                    U_step = np.load(file_path)
                    
                    # Embed U_step into a unitary matrix if it's smaller than the mesh size
                    if U_step.shape[0] < self.n or U_step.shape[1] < self.n:
                        embedded_U = np.eye(self.n, dtype=complex)
                        rows, cols = U_step.shape
                        embedded_U[:rows, :cols] = U_step
                        U_step = embedded_U

                    # 根据 Package 选项选择分解方法
                    package = self.decomposition_package_var.get()
                    if package == "pnn":
                        #from pnn.methods import decompose_clements
                        [A_phi, A_theta, *_] = decompose_clements(U_step, block='mzi')
                        A_theta *= 2 / np.pi
                        #A_phi += np.pi
                        #A_phi = A_phi % (2 * np.pi)
                        A_phi /= np.pi
                        json_output = get_json_pnn(self.n, A_theta, A_phi)
                    elif package == "interferometer":
                        I = decomposition(U_step, global_phase=use_global_phase)
                        bs_list = I.BS_list
                        clements_to_chip(bs_list)
                        json_output = get_json_interferometer(self.n, bs_list)
                    else:
                        raise ValueError(f"Unknown package: {package}")

                    # 更新 AppData.default_json_grid
                    setattr(AppData, 'default_json_grid', json_output)
                    self.update_status("  ✓ Decomposition complete", "success")

                    # 如果 Interpolation 已启用，执行插值
                    if AppData.interpolation_enabled:
                        self.update_status("  • Performing interpolation...", "info")
                        special_nodes = ["E1", "F1", "G1", "H1", "E2", "G2"]
                        from tests.interpolation.data import Reader_interpolation as reader
                        interpolated = {}
                        for node in special_nodes:
                            try:
                                theta_val = float(json_output[node]['theta'])
                                reader.load_sweep_file(f"{node}_theta_200_steps.csv")
                                interpolated_theta = reader.theta_trans(theta_val * np.pi, reader.theta, reader.theta_corrected) / np.pi
                                interpolated[node] = interpolated_theta
                                json_output[node]['theta'] = str(interpolated_theta)
                            except Exception as e:
                                self.update_status(f"  ✖ Interpolation failed for {node}: {e}", "error")
                        AppData.interpolated_theta = interpolated
                        self.update_status("  ✓ Interpolation complete", "success")

                except Exception as e:
                    self.update_status(f"  ✖ Decomposition failed: {e}", "error")
                    continue             

                # b) push phases to the chip
                self.update_status("  • Applying phases to chip...", "info")
                self.apply_phase_new()
                self.update_status("  ✓ Phases applied", "success")
                self.update()

                # Dwell time with status
                self.update_status(f"  • Waiting {dwell_ms} ms...", "info")
                num_updates = max(1, int(dwell_s * 10))
                sleep_per_update = dwell_s / num_updates
                for i in range(num_updates):
                    time.sleep(sleep_per_update)
                    self.update()

                # c) measure power
                self.update_status("  • Measuring power...", "info")

                if use_switch:
                    thorlabs_device = self.thorlabs[0] if isinstance(self.thorlabs, list) else self.thorlabs
                    measurement_values = SwitchMeasurements.measure_with_switch(
                        self.switch, thorlabs_device, switch_channels, "mW"
                    )
                else:
                    if use_source == "DAQ":
                        if self.daq:
                            daq_channels = self.daq.list_ai_channels()
                            try:
                                readings = self.daq.read_power(
                                    channels=daq_channels,
                                    samples_per_channel=samples_per_channel,
                                    sample_rate=sample_rate,
                                    unit="mW",
                                )
                                if readings and isinstance(readings[0], list):
                                    measurement_values = [sum(s)/len(s) for s in readings]
                                else:
                                    measurement_values = readings if readings else []
                            except Exception as e:
                                self.update_status(f"  ✖ DAQ read error: {e}", "error")
                                measurement_values = [0.0] * num_measurements
                            finally:
                                try:
                                    self.daq.clear_task()
                                except:
                                    pass
                        else:
                            measurement_values = [0.0] * num_measurements
                    else:  # Thorlabs
                        measurement_values = SwitchMeasurements.measure_thorlabs_direct(
                            self.thorlabs, "mW"
                        )

                # Update measurement display (for the live view)
                self.update_measurements(measurement_values, measurement_labels)
                self.update_status("  ✓ Measurement complete", "success")

                # Add measurements to the status log
                if measurement_values and measurement_labels:
                    # Format measurements inline
                    formatted_measurements = []
                    for label, value in zip(measurement_labels, measurement_values):
                        formatted_measurements.append(f"{label}: {value:.3f} µW")
                    
                    # Display measurements in the log
                    if len(formatted_measurements) <= 4:
                        # Single line for up to 4 measurements
                        self.update_status(f"  📊 {' | '.join(formatted_measurements)}", "info")
                    else:
                        # Multiple lines for more measurements
                        self.update_status("  📊 Measurements:", "info")
                        for i in range(0, len(formatted_measurements), 4):
                            line_items = formatted_measurements[i:i+4]
                            self.update_status(f"     {' | '.join(line_items)}", "info")

                # d) collect results
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                row = [timestamp, step_idx] + measurement_values
                results.append(row)

                # e) update progress bar
                self.update_progress(step_idx, total_steps)
                self.update()

            # ───────────────────────────────────────────────────────
            # 3.  Save CSV & reset chip
            # ───────────────────────────────────────────────────────
            if results:
                self.update_status("\n💾 Saving results...", "header")
                saved_path = self._export_results_to_csv(results, headers)
                if saved_path: 
                    self.update_status("✅ Results saved successfully!", "success")
                    self.update_status(f"📁 Saved to: {saved_path}", "info")
                else:
                    self.update_status("\n⚠️ Results were not saved.", "warning")
                self.update_status("\n🔄 Resetting chip to zero...", "info")
                zero_cfg = self._create_zero_config()
                apply_grid_mapping(self.qontrol, zero_cfg, self.grid_size)
                self.update_status("✅ Chip reset complete", "success")
                
                self.update_status(f"\n🎉 Experiment complete! Processed {len(results)} steps.", "success")
            else:
                self.update_status("\n⚠️ No results collected.", "warning")

        except Exception as e:
            self.update_status(f"\n❌ Experiment failed: {e}", "error")
            import traceback
            self.update_status(traceback.format_exc(), "error")
        finally:
            # Always restore button state
            self.cycle_unitaries_button.configure(text="Cycle Unitaries", state="normal")
            self.update_status(f"\nFinished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "info")

    # ──────────────────────────────────────────────────────────────
    # helper: save the results table to a CSV file
    # ──────────────────────────────────────────────────────────────
    def _export_results_to_csv(self, rows: list[list], headers: list[str]) -> None:
        """
        Ask the user where to save a CSV and write `headers` + `rows` to it.

        Parameters
        ----------
        rows    : list of list
            Each inner list is a row already in the desired order.
        headers : list of str
            Column names for the first row of the CSV.
        """
        if not rows:
            logging.debug("Nothing to export – no rows provided.")
            return None

        # default file name: cycle_results_YYYYmmdd_HHMMSS.csv
        default_name = f"cycle_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        path = filedialog.asksaveasfilename(
            title="Save Results CSV",
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:        # user pressed Cancel
            logging.debug("Export cancelled.")
            return None

        try:
            import csv
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
            logging.info(f"Results successfully saved to: {path}")
            return path
        except Exception as e:
            logging.error(f"Failed to write CSV: {e}")
            return None

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
        Apply phase settings to the entire grid based on phase calibration data from AppData.
        Processes all theta and phi values in the current grid configuration.
        """
        try:
            # Get current grid configuration
            grid_config = AppData.default_json_grid
            #logging.info(f"Current grid configuration: {grid_config}")
            if not grid_config:
                logging.warning("No grid configuration found")
                return
                
            # Get label mapping for current grid size
            create_label_mapping, apply_grid_mapping = get_mapping_functions(self.grid_size)
            label_map = create_label_mapping(int(self.grid_size.split('x')[0]))
            
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
                    
                # Process theta value
                theta_val = data.get("theta", "0")
                if theta_val:
                    try:
                        theta_float = float(theta_val)
                        calib_key = f"{cross_label}_theta"
                        current_theta = self._calculate_current_for_phase_new_json(calib_key, theta_float)
                        
                        if current_theta is not None:
                            current_theta = round(current_theta, 5)
                            phase_grid_config[cross_label]["theta"] = str(current_theta)
                            applied_channels.append(f"{cross_label}:θ = {current_theta:.5f} mA")
                        else:
                            failed_channels.append(f"{cross_label}:θ (no calibration)")
                    except Exception as e:
                        failed_channels.append(f"{cross_label}:θ ({str(e)})")

                # Process phi value
                phi_val = data.get("phi", "0")
                if phi_val:
                    try:
                        phi_float = float(phi_val)
                        calib_key = f"{cross_label}_phi"
                        current_phi = self._calculate_current_for_phase_new_json(calib_key, phi_float)
                        
                        if current_phi is not None:
                            current_phi = round(current_phi, 5)
                            phase_grid_config[cross_label]["phi"] = str(current_phi)
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
                logging.error(result_message)
                logging.error(f"Failed channels: {failed_channels}")
                
            # Debugging: Print the grid size
            #logging.info(f"Grid size: {self.grid_size}")
            
            try:
                config_json = json.dumps(phase_grid_config)
                apply_grid_mapping(self.qontrol, config_json, self.grid_size)
            except Exception as e:
                logging.error(f"Device update failed: {str(e)}")

            return phase_grid_config
            
        except Exception as e:
            logging.error(f"Failed to apply phases: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _calculate_current_for_phase_new_json(self, calib_key, phase_value):
        """
        Calculate current for a phase value using the new calibration format.
        Args:
            calib_key: str, calibration key (e.g. "A1_theta")
            phase_value: float, phase value in π units
        Returns:
            float: Current in mA or None if calculation fails
        """
        try:
            #logging.info(f"Entering _calculate_current_for_phase_new_json with calib_key={calib_key}, phase_value={phase_value}")
            
            # Get resistance calibration data
            res_cal = AppData.resistance_calibration_data.get(calib_key)
            #logging.info(f"res_cal: {res_cal}")
            if not res_cal:
                logging.error(f"No resistance calibration for {calib_key}")
                return None

            res_params = res_cal.get("resistance_params", {})
            #logging.info(f"res_params: {res_params}")
            if not res_params:
                logging.error(f"No resistance_params for {calib_key}")
                return None

            # Get phase calibration data
            phase_cal = AppData.phase_calibration_data.get(calib_key)
            #logging.info(f"phase_cal: {phase_cal}")
            if not phase_cal:
                logging.error(f"No phase calibration for {calib_key}")
                return None

            phase_params = phase_cal.get("phase_params", {})
            #logging.info(f"phase_params: {phase_params}")
            if not phase_params:
                logging.error(f"No phase_params for {calib_key}")
                return None

            # Extract parameters
            try:
                c_res = res_params['c_res']     # kΩ
                a_res = res_params['a_res']     # V/(mA)³
                alpha_res = res_params['alpha_res'] # 1/mA²
                A = phase_params['amplitude']   # mW
                b = phase_params['omega']       # rad/mW
                c = phase_params['phase']       # rad
                d = phase_params['offset']      # mW
            except Exception as e:
                logging.error(f"Failed to extract parameters: {e}")
                logging.info(f"res_params: {res_params}")
                logging.info(f"phase_params: {phase_params}")
                return None

            #logging.info(f"Extracted: c_res={c_res}, a_res={a_res}, A={A}, b={b}, c={c}, d={d}")

            if phase_value < c:
                #logging.info(f"Phase {phase_value}π is less than offset phase {c}π for {calib_key}")
                phase_value = phase_value + 2
                #logging.info(f"Using adjusted phase value: {phase_value}π")

            # Calculate heating power for this phase shift
            P_mW = abs((phase_value - c)*np.pi / b)    # Power in mW
            #logging.info(f"Calculated heating power P={P_mW} mW")
            #logging.info(f"Using parameters: A={A}, b={b}, c={c}, d={d}")

            # Define symbols for solving equation
            I = sp.symbols('I', real=True, positive=True)

            #logging.info(f"P_mW={P_mW} mW, R0={c_res} kΩ, alpha={alpha_res} (1/mA²)")

            # Define equation: P/R0 = I²(1 + alpha*I²)
            eq = sp.Eq(P_mW/c_res, I**2 * (1 + alpha_res * I**2))
            #logging.info(f"Equation: {P_mW}/{c_res} = I² × (1 + {alpha_res}×I²)")

            # Solve the equation
            solutions = sp.solve(eq, I)
            #logging.info(f"Solutions: {solutions}")

            # Filter and choose the real, positive solution
            positive_solutions = [sol.evalf() for sol in solutions if sol.is_real and sol.evalf() > 0]
            #logging.info(f"Positive solutions: {positive_solutions}")
            if positive_solutions:
                #logging.info(f"-> Calculated Current for {calib_key}: {positive_solutions[0]:.4f} mA")
                I_mA = positive_solutions[0] 
                return float(I_mA)
            else:
                logging.error(f"No positive solution for {calib_key}, fallback to linear model")
                return None

        except Exception as e:
            logging.error(f"Calculating current for {calib_key}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def decompose_unitary(self):
        """
        Load a .npy file, decompose it, and display the matrix in text format with spacing.
        """
        # Ask the user to select a .npy file
        path = filedialog.askopenfilename(
            title="Select Unitary File",
            filetypes=[("NumPy files", "*.npy")]  # Only allow .npy files
        )
        if not path:
            logging.info("No file selected. Aborting.")
            return

        try:
            # Load the unitary matrix from the .npy file
            matrix_u = np.load(path)
            #logging.info(f"Loaded unitary matrix from {path}")

            # Embed U_step into a unitary matrix if it's smaller than the mesh size
            if matrix_u.shape[0] < self.n or matrix_u.shape[1] < self.n:
                embedded_U = np.eye(self.n, dtype=complex)
                rows, cols = matrix_u.shape
                embedded_U[:rows, :cols] = matrix_u
                matrix_u = embedded_U

            # Format the matrix with additional spacing
            formatted_matrix = "\n".join(
                ["  ".join(f"{elem.real:.4f}{'+' if elem.imag >= 0 else ''}{elem.imag:.4f}j" for elem in row)
                 for row in matrix_u]
            )
            #logging.info("Formatted matrix: ")
            #logging.info(formatted_matrix)
            # Display the formatted matrix in the text box
            self.unitary_textbox.delete("1.0", "end")  # Clear the text box
            self.unitary_textbox.insert("1.0", formatted_matrix)
            

            use_global_phase = self.global_phase_var.get() # True or False
            
            package = self.decomposition_package_var.get()

            ### choose the pnn package
            if package == "pnn":
                #from pnn.methods import decompose_clements
                [A_phi, A_theta, *_] = decompose_clements(matrix_u, block = 'mzi')
                A_theta *= 2/np.pi
                #A_phi += np.pi
                #A_phi = A_phi % (2*np.pi)
                A_phi /= np.pi
                json_output = get_json_pnn(self.n, A_theta, A_phi)
            
            ### choose the interferometer package
            elif package == 'interferometer':
                I = decomposition(matrix_u, global_phase=use_global_phase)
                bs_list = I.BS_list
                clements_to_chip(bs_list)
                json_output = get_json_interferometer(self.n, bs_list)

            # Save the updated JSON to AppData
            setattr(AppData, 'default_json_grid', json_output)
            #logging.info("Updated JSON grid saved to AppData.")

        except Exception as e:
            logging.error(f"Error during decomposition: {e}")
        # Save the content inside the unitary_textbox to AppData
        AppData.unitary_textbox_content = self.unitary_textbox.get("1.0", "end").strip()
        # 如果 Interpolation 已启用，自动执行插值
        if AppData.interpolation_enabled:
            self._on_interpolation_toggle()

    def update_grid(self, new_mesh_size):
        '''Refresh NxN grids when the user selects a new mesh size.'''
        self.n = int(new_mesh_size.split('x')[0])
        self.grid_size = new_mesh_size          # keep the string in sync

