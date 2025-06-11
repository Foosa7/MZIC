# app/gui/window3.py

from app.imports import *
import tkinter.filedialog as filedialog
import copy
from app.utils.qontrol.qmapper8x8 import create_label_mapping, apply_grid_mapping
from app.utils.unitary import unitary, mzi_lut, mzi_convention
from app.utils.appdata import AppData
from app.utils.switch_measurements import SwitchMeasurements
from datetime import datetime

class Window3Content(ctk.CTkFrame):
    
    def __init__(self, master, channel, fit, IOconfig, app, qontrol, thorlabs, daq, switch, grid_size = "8x8", **kwargs):
        super().__init__(master, **kwargs)
        self.channel = channel
        self.fit = fit
        self.IOconfig = IOconfig
        self.app = app
        self.qontrol = qontrol
        self.thorlabs = thorlabs
        self.daq = daq
        self.switch = switch

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

        # ──────────────────────────────────────────────────────────────
        # 1) UNITARY-MATRIX TOOLS
        # ──────────────────────────────────────────────────────────────
        self.unitary_buttons_frame = ctk.CTkFrame(
            self.right_frame, fg_color="transparent"
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
            self.right_frame, fg_color="#2B2B2B", corner_radius=8
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

        # ─────────────────────  row – dwell-time (ms)
        ctk.CTkLabel(self.cycle_frame, text="Dwell Time (ms):")\
            .grid(row=2, column=0, sticky="e", padx=10, pady=4)

        dwell_time_frame = ctk.CTkFrame(self.cycle_frame, fg_color="transparent")
        dwell_time_frame.grid(row=2, column=1, sticky="ew", padx=10, pady=4)
        dwell_time_frame.grid_columnconfigure(0, weight=1)

        # shared state
        self.dwell_var = ctk.StringVar(value="500")   # milliseconds
        _SLIDER_MIN_MS = 1
        _SLIDER_MAX_MS = 5_000
        self._dwell_lock = False                      # recursion guard

        def _slider_moved(value_ms: float):
            if self._dwell_lock:
                return
            self._dwell_lock = True
            self.dwell_var.set(f"{int(value_ms)}")    # keep as ms
            self._dwell_lock = False

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
        self.measurement_source = ctk.StringVar(value="Thorlabs")

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
        self.decomposition_package_var = ctk.StringVar(value="interferometer")  # Default value
        self.decomposition_package_dropdown = ctk.CTkOptionMenu(
            self.cycle_frame,
            variable=self.decomposition_package_var,
            values=["interferometer", "pnn"]
        )
        self.decomposition_package_dropdown.grid(row=4, column=1, sticky="ew", padx=10, pady=4)

        # ─────────────────────  row 5 – Global Phase option
        ctk.CTkLabel(self.cycle_frame, text="Global Phase:").grid(row=5, column=0, sticky="e", padx=10, pady=4)
        self.global_phase_var = ctk.BooleanVar(value=True)  # Default: enabled
        self.global_phase_checkbox = ctk.CTkCheckBox(
            self.cycle_frame,
            text="Enable",
            variable=self.global_phase_var
        )
        self.global_phase_checkbox.grid(row=5, column=1, sticky="w", padx=10, pady=4)

        # ─────────────────────  row 6 – Measure using switch
        ctk.CTkLabel(self.cycle_frame, text="Measure using switch:")\
            .grid(row=6, column=0, sticky="e", padx=10, pady=4)

        self.measure_switch_var = ctk.StringVar(value="No")
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
        self.switch_channels_entry.insert(0, "1,2,3,4,5,6,7,8")  # Default
        self.switch_channels_entry.grid(row=7, column=1, sticky="ew", padx=10, pady=4)

        # Initially hide the channel selection
        self.switch_channels_label.grid_remove()
        self.switch_channels_entry.grid_remove()

        # ──────────────────────────────────────────────────────────────
        # 3) STATUS DISPLAY
        # ──────────────────────────────────────────────────────────────
        self.status_frame = ctk.CTkFrame(
            self.right_frame, fg_color="#1E1E1E", corner_radius=8
        )
        self.status_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
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
        
        # Progress bar
        self.progress_var = ctk.DoubleVar(value=0)
        self.progress_bar = ctk.CTkProgressBar(
            self.status_frame,
            variable=self.progress_var,
            height=20,
            corner_radius=10
        )
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 10))
        
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
        self.measurement_label.pack(fill="x", padx=10, pady=0)

        # ──────────────────────────────────────────────────────────────
        # Load any saved unitary into the entry grid
        # ──────────────────────────────────────────────────────────────
        self.handle_all_tabs()

        # Add a text box to display the matrix
        self.unitary_textbox = ctk.CTkTextbox(
            self.right_frame, width=600, height=300, wrap="none"
        )
        self.unitary_textbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def update_status(self, message, tag="info"):
        """Update the status display with a new message"""
        self.status_textbox.insert("end", f"{message}\n", tag)
        self.status_textbox.see("end")  # Auto-scroll to bottom
        self.update()
        
    def clear_status(self):
        """Clear the status display"""
        self.status_textbox.delete("1.0", "end")
        
    def update_progress(self, current, total):
        """Update the progress bar"""
        if total > 0:
            progress = (current / total) * 100
            self.progress_var.set(progress)
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
            self.progress_var.set(0)
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
                headers.extend(SwitchMeasurements.create_headers_with_switch(switch_channels, "uW"))
                num_measurements = len(switch_channels)
            else:
                # Headers for direct device measurements
                if use_source == "DAQ":
                    if self.daq:
                        daq_channels = self.daq.list_ai_channels()
                        headers.extend([f"{ch}_uW" for ch in daq_channels])
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
                        headers.extend(SwitchMeasurements.create_headers_thorlabs(num_devices, "uW"))
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

            npy_files = sorted(
                [f for f in os.listdir(folder_path)
                if f.startswith("step_") and f.endswith(".npy")],
                key=lambda x: int(x.split("_")[1].split(".")[0])
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
                
                # Update progress
                self.update_progress(step_idx - 1, total_steps)
                self.update_status(f"\n📍 Step {step_idx}/{total_steps}: {npy_file}", "info")
                
                # Update button to show progress
                self.cycle_unitaries_button.configure(text=f"Step {step_idx}/{total_steps}")
                self.update()

                # a) load the unitary + decompose → set heaters
                try:
                    self.update_status("  • Loading and decomposing unitary...", "info")
                    U_step = np.load(file_path)
                    I = unitary.decomposition(U_step, global_phase=use_global_phase)
                    bs = I.BS_list
                    mzi_convention.clements_to_chip(bs)
                    json_output = mzi_lut.get_json_output(self.n, bs)
                    setattr(AppData, 'default_json_grid', json_output)
                    self.update_status("  ✓ Decomposition complete", "success")
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
                        self.switch, thorlabs_device, switch_channels, "uW"
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
                                    unit="uW",
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
                            self.thorlabs, "uW"
                        )

                # Update measurement display
                self.update_measurements(measurement_values, measurement_labels)
                self.update_status("  ✓ Measurement complete", "success")

                # d) collect results
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                row = [timestamp, step_idx] + measurement_values
                results.append(row)

            # Update final progress
            self.update_progress(total_steps, total_steps)

            # ───────────────────────────────────────────────────────
            # 3.  Save CSV & reset chip
            # ───────────────────────────────────────────────────────
            if results:
                self.update_status("\n💾 Saving results...", "header")
                self._export_results_to_csv(results, headers)
                self.update_status("✅ Results saved successfully!", "success")

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
            print("Nothing to export – no rows provided.")
            return

        # default file name: cycle_results_YYYYmmdd_HHMMSS.csv
        default_name = f"cycle_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        path = filedialog.asksaveasfilename(
            title="Save Results CSV",
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:        # user pressed Cancel
            print("Export cancelled.")
            return

        try:
            import csv
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
            print(f"Results successfully saved to: {path}")
        except Exception as e:
            print(f"Failed to write CSV: {e}")

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

    def _update_cycle_button_state(self):
        """Enable Cycle button only if at least one site is ticked."""
        enabled = any(v.get() for v in self.site_vars)
        state = "normal" if enabled else "disabled"
        self.cycle_unitaries_button.configure(state=state)

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
        """
        Load a .npy file, decompose it, and display the matrix in text format with spacing.
        """
        # Ask the user to select a .npy file
        path = filedialog.askopenfilename(
            title="Select Unitary File",
            filetypes=[("NumPy files", "*.npy")]  # Only allow .npy files
        )
        if not path:
            print("No file selected. Aborting.")
            return

        try:
            # Load the unitary matrix from the .npy file
            matrix_u = np.load(path)
            print(f"Loaded unitary matrix from {path}")

            # Format the matrix with additional spacing
            formatted_matrix = "\n".join(
                ["  ".join(f"{elem.real:.4f}{'+' if elem.imag >= 0 else ''}{elem.imag:.4f}j" for elem in row)
                 for row in matrix_u]
            )
            print("Formatted matrix: ")
            print(formatted_matrix)
            # Display the formatted matrix in the text box
            self.unitary_textbox.delete("1.0", "end")  # Clear the text box
            self.unitary_textbox.insert("1.0", formatted_matrix)

            use_global_phase = self.global_phase_var.get() # True or False

            # Perform decomposition
            I = unitary.decomposition(matrix_u, global_phase=use_global_phase)
            bs_list = I.BS_list
            mzi_convention.clements_to_chip(bs_list)

            # Update the AppData with the new JSON output
            input_pin = int(self.input_var.get())
            output_pin = int(self.output_var.get())
            json_output = mzi_lut.get_json_output(self.n, bs_list, input_pin, output_pin)
            print(json_output)

            # Save the updated JSON to AppData
            setattr(AppData, 'default_json_grid', json_output)
            print("Updated JSON grid saved to AppData.")

        except Exception as e:
            print(f"Error during decomposition: {e}")

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
        mat = unitary.random_unitary(self.n)
    
        entries, appdata_var = self.get_active_tab()  # Get active tab dynamically
    
        if entries is not None and appdata_var is not None:
            self.fill_tab_entries(entries, mat)
            setattr(AppData, appdata_var, mat)  # Save dynamically

    def update_grid(self, new_mesh_size):
        '''Refresh NxN grids when the user selects a new mesh size.'''
        self.n = int(new_mesh_size.split('x')[0])
        self.grid_size = new_mesh_size          # keep the string in sync

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