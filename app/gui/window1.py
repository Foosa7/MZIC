# app/gui/window1.py
from app.imports import *

from decimal import *
import copy
import sympy as sp
from app.utils.appdata import AppData
import io
from contextlib import redirect_stdout
from app.gui.widgets import PhaseShifterSelectionWidget
import customtkinter as ctk
from app.utils import grid
from app.utils.qontrol.qmapper8x8 import create_label_mapping, apply_grid_mapping
from collections import defaultdict
from typing import Dict, Any
from scipy import optimize
from app.devices.switch_device import Switch

class Window1Content(ctk.CTkFrame):
    ### Define the callbacks for the interpolation functionality and update the label###
    def _on_interpolate_theta_toggle(self):
        """Enable/disable interpolation and update theta values for 6 nodes."""
        self.interpolation_enabled = self.interpolate_theta_var.get()
        if self.interpolation_enabled:
            # List of 6 special nodes
            special_nodes = ["E1", "F1", "G1", "H1", "E2", "G2"]
            from tests.interpolation.data import Reader_interpolation as reader
            updated = []
            for node in special_nodes:
                # Get current theta value from the grid
                try:
                    theta_val = float(self.custom_grid.input_boxes[node]['theta_entry'].get())
                except Exception:
                    continue
                # Do interpolation (replace with your actual logic)
                reader.load_sweep_file(f"{node}_theta_200_steps.csv")
                interpolated = reader.theta_trans(theta_val * np.pi, reader.theta, reader.theta_corrected) / np.pi
                self.interpolated_theta[node] = interpolated
                updated.append(f"{node}: {interpolated:.3f}")
            # Show updated values
            self.interpolated_theta_label.configure(text="; ".join(updated) if updated else "No valid theta found")
        else:
            self.interpolated_theta.clear()
            self.interpolated_theta_label.configure(text="")
        ######




    def __init__(self, master, channel, fit, IOconfig, app, qontrol, thorlabs, daq, switch, phase_selector=None, grid_size="8x8", **kwargs):
        super().__init__(master, **kwargs)
        self.qontrol = qontrol
        self.thorlabs = thorlabs
        self.daq = daq   
        self.switch = switch     
        self.grid_size = grid_size
        self.after_id = None
        self.control_panel = None  
        self.resistance_params: Dict[int, Dict[str, Any]] = {}
        self.calibration_params = {'cross': {}, 'bar': {}}
        self.phase_params = {}
        #### Add the interpolation functionality ####
        self.interpolation_enabled = False
        self.interpolated_theta = {}  # e.g., {"E1": 0.987, ...}
        
        self.phase_selector = phase_selector
        self.app = app  # Store the AppData instance

        # Initialize interpolation manager
        from app.utils.interpolation import interpolation_manager
        self.interpolation_manager = interpolation_manager

        # Configure main layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create main container with adjusted column weights
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        # Adjust column weights to give more space to grid (4:1 ratio)
        self.main_frame.grid_columnconfigure(0, weight=4)  # 80% for grid
        self.main_frame.grid_columnconfigure(1, weight=1)  # 20% for controls
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Build UI components
        self._create_grid_container()
        self._create_compact_control_panel()  # Changed to compact version
        # self._create_calibration_controls()
        self._create_status_displays()
        
        # Initial setup
        self.build_grid(self.grid_size)
        self.custom_grid.master = self.grid_container  # Explicit parent assignment
        self._start_status_updates()
        # self._update_selection_display()
        self._setup_event_bindings()

        self.selected_unit = "uW"  # Default unit for power measurement

        self._initialize_live_graph() # Initialize the live graph

    def _create_grid_container(self):
        """Create expanded grid display area"""
        self.grid_container = ctk.CTkFrame(self.main_frame)
        self.grid_container.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.grid_container.grid_rowconfigure(0, weight=1)
        self.grid_container.grid_columnconfigure(0, weight=1)

    def _create_compact_control_panel(self):
        """Create compact right-side control panel"""
        control_frame = ctk.CTkFrame(self.main_frame)
        control_frame.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        control_frame.grid_rowconfigure(0, weight=1)
        control_frame.grid_columnconfigure(0, weight=1)
        # self.graph_frame.pack_propagate(False)
        
        # Compact inner frame
        inner_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        inner_frame.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        inner_frame.grid_rowconfigure(1, weight=1)

        # Compact button row
        btn_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 2))

        # # Original controls + new calibration buttons
        # controls = [
        #     ("Import", self._import_config),
        #     ("Export", self._export_config),
        #     ("Apply", self._apply_config),
        #     ("Clear", self._clear_grid),
        #     ("Status", self._show_full_status),
        #     ("R", self._run_resistance_calibration),
        #     ("P", self._run_phase_calibration)
        # ]

        # Add to your controls list in _create_compact_control_panel method:
        controls = [
            ("Import", self._import_config),
            ("Export", self._export_config),
            ("Current", self._apply_config),
            ("Clear", self._clear_grid),
            # ("Status", self._show_full_status),
            ("R", self._run_resistance_calibration),
            ("P", self._run_phase_calibration),
            ("Phase", self.apply_phase_new)  # Add this new button
        ]

        for col in range(7):
            btn_frame.grid_columnconfigure(col, weight=1)

        # Create buttons with adjusted styling
        for col, (text, cmd) in enumerate(controls):
            btn = ctk.CTkButton(
                btn_frame, 
                text=text,
                command=cmd,
                width=20, 
                height=24,
                font=ctk.CTkFont(size=12) 
            )
            btn.grid(row=0, column=col, padx=1, sticky="nsew")

        # Interpolate Theta toggle
        self.interpolate_theta_var = ctk.BooleanVar(value=False)
        self.interpolate_theta_button = ctk.CTkCheckBox(
            btn_frame,
            text="Interpolate Theta (6 nodes)",
            variable=self.interpolate_theta_var,
            command=self._on_interpolate_theta_toggle
        )
        self.interpolate_theta_button.grid(row=1, column=0, columnspan=7, sticky="ew", pady=(5, 0))

        # Label to show updated values
        self.interpolated_theta_label = ctk.CTkLabel(btn_frame, text="")
        self.interpolated_theta_label.grid(row=2, column=0, columnspan=7, sticky="ew")

        # Compact notebook for displays
        notebook = ctk.CTkTabview(inner_frame, height=180, width=300)  # Fixed height, width
        notebook.grid_propagate(False)
        notebook.grid(row=1, column=0, sticky="nsew", pady=(2, 0))
        inner_frame.grid_columnconfigure(0, weight=1)

        ### Interpolation tab ###
        interpolation_tab = notebook.add("Interpolation")
        interpolation_tab.grid_columnconfigure(0, weight=1)
        interpolation_tab.grid_columnconfigure(1, weight=2)  # Give more space to the dropdown column
        interpolation_tab.grid_rowconfigure(7, weight=1)  # For the plot area

        # Row 0: Enable Interpolation
        option_a_label = ctk.CTkLabel(interpolation_tab, text="Enable Interpolation:")
        option_a_label.grid(row=0, column=0, padx=(10, 5), pady=(10, 5), sticky="w")

        self.interp_option_a = ctk.CTkOptionMenu(interpolation_tab,
                                                values=["enable", "disable"],
                                                command=self._on_interpolation_option_changed)
        self.interp_option_a.set("disable")
        self.interp_option_a.grid(row=0, column=1, padx=(5, 10), pady=(10, 5), sticky="ew")

        # Row 1: Satisfy sweep files?
        option_b_label = ctk.CTkLabel(interpolation_tab, text="Satisfy sweep files?")
        option_b_label.grid(row=1, column=0, padx=(10, 5), pady=5, sticky="w")

        self.interp_option_b = ctk.CTkOptionMenu(interpolation_tab,
                                                values=["satisfy with sweep files", "Not satisfy"],
                                                command=self._on_interpolation_option_changed)
        self.interp_option_b.set("Not satisfy")
        self.interp_option_b.grid(row=1, column=1, padx=(5, 10), pady=5, sticky="ew")

        # Row 2: Sweep file
        file_label = ctk.CTkLabel(interpolation_tab, text="Sweep file:")
        file_label.grid(row=2, column=0, padx=(10, 5), pady=5, sticky="w")

        # Get available files from interpolation manager
        available_files = self.interpolation_manager.get_available_files()
        if not available_files:
            available_files = ["No files available"]
            default_file = "No files available"
        else:
            default_file = available_files[0]

        self.sweep_file_menu = ctk.CTkOptionMenu(
            interpolation_tab,
            values=available_files,
            command=self._on_sweep_file_changed
        )
        self.sweep_file_menu.set(default_file)
        self.sweep_file_menu.grid(row=2, column=1, padx=(5, 10), pady=5, sticky="ew")

        # Row 3: Separator line (optional, for visual clarity)
        separator = ctk.CTkFrame(interpolation_tab, height=2)
        separator.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))

        # Row 4: Input angle
        angle_label = ctk.CTkLabel(interpolation_tab, text="Input angle (π radians):")
        angle_label.grid(row=4, column=0, padx=(10, 5), pady=5, sticky="w")

        self.angle_entry = ctk.CTkEntry(interpolation_tab, placeholder_text="e.g., 1.57")
        self.angle_entry.grid(row=4, column=1, padx=(5, 10), pady=5, sticky="ew")

        # Row 5: Plot button
        self.plot_button = ctk.CTkButton(
            interpolation_tab,
            text="Plot",
            command=self._on_plot_interpolation
        )
        self.plot_button.grid(row=5, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="ew")

        # Row 6: Plot area
        self.interp_plot_label = ctk.CTkLabel(interpolation_tab, text="No image yet")
        self.interp_plot_label.grid(row=6, column=0, columnspan=2, padx=10, pady=(5, 10), sticky="nsew")

        # Load the default file if it's available
        if default_file != "No files available":
            try:
                self.interpolation_manager.load_sweep_file(default_file)
                print(f"[Interpolation] Default file loaded: {default_file}")
                self.interp_plot_label.configure(text=f"File loaded: {default_file}")
            except Exception as e:
                print(f"[Interpolation] Failed to load default file: {e}")
                self.interp_plot_label.configure(text="Failed to load default file")

        # Initialize the proper state of controls based on the initial settings
        self._on_interpolation_option_changed()

        ### Mapping tab ###
        self.mapping_display = ctk.CTkTextbox(notebook.add("Mapping"))
        self.mapping_display.pack(fill="both", expand=True)

        ### Monitor tab ###
        monitor_tab = notebook.add("Monitor")
        monitor_tab.grid_columnconfigure(0, weight=1)
        monitor_tab.grid_rowconfigure(0, weight=1)  # Row for the live graph
        monitor_tab.grid_rowconfigure(1, weight=0)  # Row for the text box
        monitor_tab.grid_rowconfigure(2, weight=0)  # Row for the buttons

        # Live Graph Frame (top part of Monitor tab)
        self.live_graph_frame = ctk.CTkFrame(monitor_tab, height=300)
        self.live_graph_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Shared Textbox for both DAQ + Thorlabs readings (middle part of Measure tab)
        self.measurement_text_box = ctk.CTkTextbox(monitor_tab, state="disabled")
        self.measurement_text_box.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Button + Sample Entry Frame (bottom part of Monitor tab) - Approach 3: Two-row layout
        measure_button_frame = ctk.CTkFrame(monitor_tab)
        measure_button_frame.grid(row=2, column=0, sticky="ew")

        # First row: Read Devices, Start/Stop
        row0_frame = ctk.CTkFrame(measure_button_frame)
        row0_frame.pack(fill="x", pady=2)

        self.read_daq_button = ctk.CTkButton(
            row0_frame,
            text="Read Devices",
            command=self._read_all_measurements
        )
        self.read_daq_button.pack(side="left", padx=5, pady=5)

        self.toggle_graph_button = ctk.CTkButton(
            row0_frame,
            text="Start/Stop Graph",
            command=self._toggle_live_graph
        )
        self.toggle_graph_button.pack(side="left", padx=5, pady=5)

        self.export_graph_button = ctk.CTkButton(
            row0_frame,
            text="Export Graph",
            command=self._export_live_graph  # Add the export functionality
        )
        self.export_graph_button.pack(side="left", padx=5, pady=5)

        # Second row: Units label, Unit selector, and Samples entry
        row1_frame = ctk.CTkFrame(measure_button_frame)
        row1_frame.pack(fill="x", pady=2)
        unit_label = ctk.CTkLabel(row1_frame, text="Units:", anchor="w")
        unit_label.pack(side="left", padx=5, pady=5)
        self.unit_selector = ctk.CTkOptionMenu(row1_frame,
                                               values=["uW", "mW", "W"],
                                               command=self._update_selected_unit,
                                               width=30)
        self.unit_selector.set("uW")
        self.unit_selector.pack(side="left", padx=5, pady=5)
        self.samples_entry = ctk.CTkEntry(row1_frame,
                                          width=65,
                                          placeholder_text="Samples")
        self.samples_entry.pack(side="left", padx=5, pady=5)

        # --- Add input for path sequence, delay, and run button ---
        self.path_sequence_entry = ctk.CTkEntry(row1_frame,
                                                width=180,
                                                placeholder_text="Paste JSON lines here")
        self.path_sequence_entry.pack(side="left", padx=5, pady=5)

        self.delay_entry = ctk.CTkEntry(row1_frame,
                                        width=60,
                                        placeholder_text="Delay (s)")
        self.delay_entry.insert(0, "0.5")
        self.delay_entry.pack(side="left", padx=5, pady=5)

        self.run_path_sequence_button = ctk.CTkButton(
            row1_frame,
            text="Run Path Sequence",
            command=self._on_run_path_sequence
        )
        self.run_path_sequence_button.pack(side="left", padx=5, pady=5)

        ### Graph tab ###
        graph_tab = notebook.add("R/P Graph")
        self.graph_frame = ctk.CTkFrame(graph_tab)
        self.graph_frame.grid(row=0, column=0, sticky="nsew")
        
        graph_tab.grid_rowconfigure(0, weight=1)
        graph_tab.grid_columnconfigure(0, weight=1)
        
        self.graph_frame.grid_rowconfigure(0, weight=1) # Plot 1
        self.graph_frame.grid_rowconfigure(1, weight=1) # Plot 2
        self.graph_frame.grid_columnconfigure(0, weight=1)

        self.graph_image_label1 = ctk.CTkLabel(
            self.graph_frame, text="No plot to display", anchor="n"
        )
        self.graph_image_label1.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        self.graph_image_label2 = ctk.CTkLabel(
            self.graph_frame, text="No plot to display", anchor="n" 
        )
        self.graph_image_label2.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)

        ### Status tab ###
        self.status_display = ctk.CTkTextbox(notebook.add("Status"), state="disabled")
        self.status_display.pack(fill="both", expand=True)
                
        ### Sweep tab ###
        sweep_tab = notebook.add("Sweep")
        sweep_tab.grid_columnconfigure(0, weight=1)
        sweep_tab.grid_columnconfigure(1, weight=1)
        
        # Row 0: Target MZI entry
        target_label = ctk.CTkLabel(sweep_tab, text="Target MZI:")
        target_label.grid(row=0, column=0, padx=(10, 5), pady=(10, 5), sticky="w")
        
        self.sweep_target_entry = ctk.CTkEntry(sweep_tab, placeholder_text="e.g. A1")
        self.sweep_target_entry.grid(row=0, column=1, padx=(5, 10), pady=(10, 5), sticky="ew")
        
        # Row 1: Theta/Phi selection
        parameter_label = ctk.CTkLabel(sweep_tab, text="Parameter:")
        parameter_label.grid(row=1, column=0, padx=(10, 5), pady=5, sticky="w")
        
        self.sweep_parameter_menu = ctk.CTkOptionMenu(
            sweep_tab,
            values=["theta", "phi"]
        )
        self.sweep_parameter_menu.set("theta")
        self.sweep_parameter_menu.grid(row=1, column=1, padx=(5, 10), pady=5, sticky="ew")
        
        # Row 2: Start value
        start_label = ctk.CTkLabel(sweep_tab, text="Start (π):")
        start_label.grid(row=2, column=0, padx=(10, 5), pady=5, sticky="w")
        
        self.sweep_start_entry = ctk.CTkEntry(sweep_tab, placeholder_text="0.0")
        self.sweep_start_entry.insert(0, "0.0")
        self.sweep_start_entry.grid(row=2, column=1, padx=(5, 10), pady=5, sticky="ew")
        
        # Row 3: End value
        end_label = ctk.CTkLabel(sweep_tab, text="End (π):")
        end_label.grid(row=3, column=0, padx=(10, 5), pady=5, sticky="w")
        
        self.sweep_end_entry = ctk.CTkEntry(sweep_tab, placeholder_text="2.0")
        self.sweep_end_entry.insert(0, "2.0")
        self.sweep_end_entry.grid(row=3, column=1, padx=(5, 10), pady=5, sticky="ew")
        
        # Row 4: Number of steps
        steps_label = ctk.CTkLabel(sweep_tab, text="Steps:")
        steps_label.grid(row=4, column=0, padx=(10, 5), pady=5, sticky="w")
        
        self.sweep_steps_entry = ctk.CTkEntry(sweep_tab, placeholder_text="20")
        self.sweep_steps_entry.insert(0, "20")
        self.sweep_steps_entry.grid(row=4, column=1, padx=(5, 10), pady=5, sticky="ew")
        
        # Row 5: Dwell time
        dwell_label = ctk.CTkLabel(sweep_tab, text="Dwell time (ms):")
        dwell_label.grid(row=5, column=0, padx=(10, 5), pady=5, sticky="w")
        
        self.sweep_dwell_entry = ctk.CTkEntry(sweep_tab, placeholder_text="1e3")
        self.sweep_dwell_entry.insert(0, "1e3")  # Default to 1000 ms (1 second)
        self.sweep_dwell_entry.grid(row=5, column=1, padx=(5, 10), pady=5, sticky="ew")

        # Row 6: Measure using switch
        measure_label = ctk.CTkLabel(sweep_tab, text="Measure using switch:")
        measure_label.grid(row=6, column=0, padx=(10, 5), pady=5, sticky="w")
        
        self.measure_switch_menu = ctk.CTkOptionMenu(
            sweep_tab,
            values=["Yes", "No"],
            command=lambda value: setattr(self, 'measure_using_switch', value)
        )
        self.measure_switch_menu.set("No")  # Default to "No"
        self.measure_switch_menu.grid(row=6, column=1, padx=(5, 10), pady=5, sticky="ew")

        # Row 7: Switch channels entry (only shown when "Yes" is selected)
        self.switch_channels_label = ctk.CTkLabel(sweep_tab, text="Switch channels (comma-separated):")
        self.switch_channels_label.grid(row=7, column=0, padx=(10, 5), pady=5, sticky="w")

        self.switch_channels_entry = ctk.CTkEntry(sweep_tab, placeholder_text="e.g., 1,2,3,4 or 1-8")
        self.switch_channels_entry.insert(0, "1,2,3,4,5,6,7,8")  # Default to channels 1-8
        self.switch_channels_entry.grid(row=7, column=1, padx=(5, 10), pady=5, sticky="ew")

        # Initially hide the channel selection
        self.switch_channels_label.grid_remove()
        self.switch_channels_entry.grid_remove()

        # Update the measure_switch_menu callback to show/hide channel selection
        self.measure_switch_menu = ctk.CTkOptionMenu(
            sweep_tab,
            values=["Yes", "No"],
            command=self._on_measure_switch_changed
        )
        self.measure_switch_menu.set("No")  # Default to "No"
        self.measure_switch_menu.grid(row=6, column=1, padx=(5, 10), pady=5, sticky="ew")

        # Row 8: Run button (update row number)
        self.sweep_run_button = ctk.CTkButton(
            sweep_tab,
            text="Run Sweep",
            command=self._run_sweep
        )
        self.sweep_run_button.grid(row=8, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        ### Switch tab ###
        switch_tab = notebook.add("Switch")
        switch_tab.grid_columnconfigure(0, weight=1)
        switch_tab.grid_columnconfigure(1, weight=1)

        # Row 0: Channel selection
        channel_label = ctk.CTkLabel(switch_tab, text="Channel:")
        channel_label.grid(row=0, column=0, padx=(10, 5), pady=(10, 5), sticky="w")

        self.switch_channel_entry = ctk.CTkEntry(switch_tab, placeholder_text="1-12")
        self.switch_channel_entry.grid(row=0, column=1, padx=(5, 10), pady=(10, 5), sticky="ew")

        # Row 1: Set channel button
        self.switch_set_button = ctk.CTkButton(
            switch_tab,
            text="Set Channel",
            command=self._set_switch_channel
        )
        self.switch_set_button.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        # Row 2: Get current channel button
        self.switch_get_button = ctk.CTkButton(
            switch_tab,
            text="Get Current Channel",
            command=self._get_switch_channel
        )
        self.switch_get_button.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        # Row 3: Current channel display
        self.switch_status_label = ctk.CTkLabel(
            switch_tab, 
            text="Current Channel: Unknown",
            font=("TkDefaultFont", 12, "bold")
        )
        self.switch_status_label.grid(row=3, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="ew")

        # Row 4: Quick channel buttons (1-8)
        quick_frame = ctk.CTkFrame(switch_tab, fg_color="transparent")
        quick_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="ew")

        quick_label = ctk.CTkLabel(quick_frame, text="Quick Select:")
        quick_label.pack(side="left", padx=(0, 10))

        for i in range(1, 9):
            btn = ctk.CTkButton(
                quick_frame,
                text=str(i),
                width=30,
                command=lambda ch=i: self._quick_set_channel(ch)
            )
            btn.pack(side="left", padx=2)

        # Compact error display in inner_frame
        self.error_display = ctk.CTkTextbox(inner_frame, height=100, state="disabled")
        self.error_display.grid(row=2, column=0, sticky="ew", pady=(2, 0))
    
    def _on_measure_switch_changed(self, value):
        """Show/hide switch channel selection based on measure option"""
        if value == "Yes":
            self.switch_channels_label.grid()
            self.switch_channels_entry.grid()
        else:
            self.switch_channels_label.grid_remove()
            self.switch_channels_entry.grid_remove()

    def _parse_switch_channels(self, channel_string):
        """
        Parse channel string input to get list of channel numbers.
        Supports formats like "1,2,3,4" or "1-4" or "1-4,7,9-12"
        
        Args:
            channel_string (str): User input for channels
            
        Returns:
            list: List of channel numbers
        """
        channels = []
        
        try:
            # Split by comma first
            parts = channel_string.replace(" ", "").split(",")
            
            for part in parts:
                if "-" in part:
                    # Handle range like "1-4"
                    start, end = part.split("-")
                    channels.extend(range(int(start), int(end) + 1))
                else:
                    # Handle single channel
                    channels.append(int(part))
            
            # Remove duplicates and sort
            channels = sorted(list(set(channels)))
            
            # Validate channel numbers (assuming 1-12 for your switch)
            valid_channels = [ch for ch in channels if 1 <= ch <= 12]
            
            if len(valid_channels) != len(channels):
                print(f"Warning: Some channels were out of range (1-12). Using: {valid_channels}")
                
            return valid_channels
            
        except Exception as e:
            raise ValueError(f"Invalid channel format: {channel_string}. Use format like '1,2,3,4' or '1-8'")

    def _set_switch_channel(self):
        """Set the switch to the specified channel"""
        if not self.switch:
            self._show_error("Switch device not connected")
            return
            
        try:
            channel = int(self.switch_channel_entry.get())
            if not (1 <= channel <= 12):  # Adjust range based on your switch
                raise ValueError("Channel must be between 1 and 12")
                
            # Set the channel
            self.switch.set_channel(channel)
            
            # Verify it was set
            time.sleep(0.1)  # Small delay
            current = self.switch.get_channel()
            
            if current == channel:
                self.switch_status_label.configure(
                    text=f"Current Channel: {current} ✓",
                    text_color="green"
                )
            else:
                self.switch_status_label.configure(
                    text=f"Current Channel: {current} (Failed to set {channel})",
                    text_color="red"
                )
                
        except ValueError as e:
            self._show_error(f"Invalid channel: {e}")
        except Exception as e:
            self._show_error(f"Failed to set channel: {e}")

    def _get_switch_channel(self):
        """Get the current channel from the switch"""
        if not self.switch:
            self._show_error("Switch device not connected")
            return
            
        try:
            channel = self.switch.get_channel()
            if channel is not None:
                self.switch_status_label.configure(
                    text=f"Current Channel: {channel}",
                    text_color="white"
                )
                self.switch_channel_entry.delete(0, "end")
                self.switch_channel_entry.insert(0, str(channel))
            else:
                self.switch_status_label.configure(
                    text="Failed to read channel",
                    text_color="red"
                )
        except Exception as e:
            self._show_error(f"Failed to read channel: {e}")

    def _quick_set_channel(self, channel):
        """Quick set channel using numbered buttons"""
        self.switch_channel_entry.delete(0, "end")
        self.switch_channel_entry.insert(0, str(channel))
        self._set_switch_channel()

    def _run_sweep(self):
        """Run MZI Sweep with configurable switch channel measurement"""
        try:
            # Get parameters
            target_mzi = self.sweep_target_entry.get().strip().upper()
            parameter = self.sweep_parameter_menu.get()
            start_val = float(self.sweep_start_entry.get())
            end_val = float(self.sweep_end_entry.get())
            num_steps = int(self.sweep_steps_entry.get())
            dwell_time = float(self.sweep_dwell_entry.get()) / 1000  # Convert ms to seconds
            use_switch = True if self.measure_switch_menu.get() == "Yes" else False
            
            # Validate MZI format (e.g., A1, B2, etc.)
            if not re.match(r"^[A-Z][0-9]+$", target_mzi):
                raise ValueError("Invalid MZI format. Use format like 'A1'")
            
            if num_steps <= 0:
                raise ValueError("Number of steps must be positive")
            
            # Get switch channels if using switch
            if use_switch:
                if not self.switch:
                    raise ValueError("Switch device not available but 'Measure using switch' is selected")
                
                # Parse user-specified channels
                channel_string = self.switch_channels_entry.get()
                self.switch_channels = self._parse_switch_channels(channel_string)
                
                if not self.switch_channels:
                    raise ValueError("No valid switch channels specified")
                    
                print(f"  Using switch channels: {self.switch_channels}")
            
            # Get the current grid configuration as JSON
            base_json = self.custom_grid.export_paths_json()
            
            # Update status
            self.sweep_run_button.configure(state="disabled")
            
            # Generate sweep values
            sweep_values = np.linspace(start_val, end_val, num_steps)
            
            print(f"\nStarting sweep:")
            print(f"  Target MZI: {target_mzi}")
            print(f"  Parameter: {parameter}")
            print(f"  Range: {start_val}π to {end_val}π")
            print(f"  Steps: {num_steps}")
            print(f"  Dwell time: {dwell_time} seconds")
            print(f"  Using switch: {use_switch}")
            
            # Initialize results storage
            self.sweep_results = []
            headers = self._create_sweep_headers(parameter, use_switch)
            
            for i, value in enumerate(sweep_values):
                print(f"  Step {i+1}/{num_steps}: {parameter} = {value:.3f}π")
                
                # Update the json for the target MZI
                updated_json = self.update_mzi_in_json(base_json, target_mzi, parameter, str(value))
                print(updated_json)
                
                self.update()  # Allow Tkinter to process GUI updates
                
                self.custom_grid.import_paths_json(updated_json)
                
                # Apply the phase configuration
                self.apply_phase_new()
                
                time.sleep(dwell_time)  # Dwell time for system to settle
                
                # Take measurements after dwell time
                measurements = self._take_sweep_measurements(use_switch)
                
                # Store results
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                result_row = [timestamp, i + 1, f"{value:.6f}"]
                result_row.extend([f"{m:.6f}" for m in measurements])
                self.sweep_results.append(result_row)
                
                # Print current measurements
                self._print_sweep_measurements(measurements, use_switch)
            
            # Export results
            if self.sweep_results:
                self._export_results_to_csv(self.sweep_results, headers)
            
            # Reset UI
            self.sweep_run_button.configure(state="normal")
            print("\nSweep complete!")
            
        except ValueError as e:
            self._show_error(str(e))
            self.sweep_run_button.configure(state="normal")
        except Exception as e:
            self._show_error(f"Sweep failed: {str(e)}")
            self.sweep_run_button.configure(state="normal")

    def _create_sweep_headers(self, parameter, use_switch):
        """Create headers for sweep results based on measurement type"""
        headers = ["timestamp", "step", f"{parameter}_pi_units"]
        
        if use_switch:
            # Use the user-specified channels stored in self.switch_channels
            for ch in self.switch_channels:
                headers.append(f"ch{ch}_{self.selected_unit}")
        else:
            # Headers for direct Thorlabs measurements
            if self.thorlabs:
                devices = self.thorlabs if isinstance(self.thorlabs, list) else [self.thorlabs]
                for i in range(len(devices)):
                    headers.append(f"thorlabs{i}_{self.selected_unit}")
        
        return headers

    def _take_sweep_measurements(self, use_switch):
        """
        Take measurements using either switch or direct Thorlabs readings
        
        Args:
            use_switch (bool): Whether to use the optical switch
            
        Returns:
            list: Power measurements
        """
        if use_switch:
            return self._measure_with_switch()
        else:
            return self._measure_thorlabs_direct()

    def _measure_with_switch(self):
        """Measure power using the optical switch for specified channels only"""
        measurements = []
        
        if not self.switch or not self.thorlabs:
            print("    Error: Switch or Thorlabs device not available")
            return measurements
        
        # Get the first Thorlabs device (connected to switch output)
        thorlabs_device = self.thorlabs[0] if isinstance(self.thorlabs, list) else self.thorlabs
        
        # Measure only the specified switch channels
        for channel in self.switch_channels:
            try:
                # Set switch to channel
                self.switch.set_channel(channel)
                
                # Small delay to allow switch to settle
                time.sleep(0.05)  # 50ms settling time
                
                # Read power
                power = thorlabs_device.read_power(unit=self.selected_unit)
                measurements.append(power)
                
            except Exception as e:
                print(f"    Error measuring channel {channel}: {e}")
                measurements.append(0.0)
        
        return measurements

    def _measure_thorlabs_direct(self):
        """Measure power directly from Thorlabs devices (no switch)"""
        measurements = []
        
        if not self.thorlabs:
            print("    Error: No Thorlabs devices available")
            return measurements
        
        devices = self.thorlabs if isinstance(self.thorlabs, list) else [self.thorlabs]
        
        for i, device in enumerate(devices):
            try:
                power = device.read_power(unit=self.selected_unit)
                measurements.append(power)
            except Exception as e:
                print(f"    Error reading Thorlabs {i}: {e}")
                measurements.append(0.0)
        
        return measurements

    def _print_sweep_measurements(self, measurements, use_switch):
        """Print measurements to console"""
        if use_switch:
            print("    Switch measurements:")
            for i, (ch, power) in enumerate(zip(self.switch_channels, measurements)):
                print(f"      Channel {ch}: {power:.3f} {self.selected_unit}")
        else:
            print("    Thorlabs measurements:")
            for i, power in enumerate(measurements):
                print(f"      Device {i}: {power:.3f} {self.selected_unit}")

    def update_mzi_in_json(self, json_string, target_mzi, parameter, value):
        """
        Update the target MZI in the JSON string while leaving everything else unchanged.

        Args:
            json_string (str): The original JSON string.
            target_mzi (str): The MZI label to update (e.g., "A1").
            parameter (str): The parameter to update (e.g., "theta" or "phi").
            value (str): The new value for the parameter.

        Returns:
            str: The updated JSON string.
        """
        try:
            # Parse the JSON string into a dictionary
            grid_config = json.loads(json_string)

            # Check if the target MZI exists in the dictionary
            if target_mzi not in grid_config:
                print(f"[INFO] Target MZI '{target_mzi}' not found. Adding it with default values.")
                # Add the target MZI with default values
                grid_config[target_mzi] = {
                    "arms": ["TL", "BR"],  
                    "theta": "0.0",       # placeholder
                    "phi": "0.0"          # placeholder
            }

            # Update the specified parameter for the target MZI
            if parameter in grid_config[target_mzi]:
                grid_config[target_mzi][parameter] = value
            else:
                raise ValueError(f"Parameter '{parameter}' not found in MZI '{target_mzi}'.")

            # Convert the dictionary back into a JSON string
            updated_json_string = json.dumps(grid_config, indent=4)
            return updated_json_string
        except Exception as e:
            print(f"[ERROR] Failed to update target MZI: {e}")
            return json_string  # Return the original JSON string if an error occurs

    def _on_interpolation_option_changed(self, value=None):
        """Handle changes to interpolation tab options."""
        a = self.interp_option_a.get()
        b = self.interp_option_b.get()

        print(f"[Interpolation] Option A: {a}, Option B: {b}")

        # Define workflow based on (a, b)
        if a == "enable" and b == "satisfy with sweep files":
            print("→ Run workflow: Interpolation + Sweep compatibility")
            # self._run_interpolation_with_sweep()  # replace with actual method
        elif a == "enable" and b == "Not satisfy":
            print("→ Run workflow: Interpolation only")
            # self._run_interpolation_without_sweep()
        elif a == "disable":
            print("→ Interpolation disabled")
            # self._disable_interpolation()

    def _on_run_path_sequence(self):
        """
        Handler for the Run Path Sequence button.
        Expects multiple JSON lines in the entry, one per line.
        """
        import json
        raw = self.path_sequence_entry.get()
        delay_raw = self.delay_entry.get()
        if not raw.strip():
            self._show_error("Please paste JSON lines for the path sequence.")
            return
        try:
            delay = float(delay_raw)
            if delay < 0:
                raise ValueError("Delay must be non-negative.")
        except Exception as e:
            self._show_error(f"Invalid delay value: {e}")
            return
        try:
            # Support multi-line input: each line is a JSON dict
            lines = [line for line in raw.strip().splitlines() if line.strip()]
            path_list = [json.loads(line) for line in lines]
        except Exception as e:
            self._show_error(f"Invalid JSON input: {e}")
            return
        self.run_path_sequence(path_list, delay=delay)

    def run_path_sequence(self, path_list, delay=0.5):
        """
        Run each path (JSON dict) in path_list with a delay between each.
        Applies phase logic for each step.
        Measures from 2 Thorlabs devices after each step and saves results to CSV at the end.
        """
        import json
        from datetime import datetime

        results = []
        headers = ["timestamp", "step", "thorlabs1_uW", "thorlabs2_uW"]

        def run_next(index):
            if index >= len(path_list):
                # Export results
                if results:
                    self._export_results_to_csv(results, headers)
                    print("\nPath sequence complete!")
                    # Reset phases to zero
                    zero_config = self._create_zero_config()
                    apply_grid_mapping(self.qontrol, zero_config, self.grid_size)
                    print("All values reset to zero")
                else:
                    print("\nNo measurements collected.")
                return

            # Update the global grid config
            AppData.default_json_grid = path_list[index]
            print(f"Applying path {index+1}/{len(path_list)}: {AppData.default_json_grid}")
            # Optionally update the grid UI
            self.custom_grid.import_paths_json(json.dumps(AppData.default_json_grid))
            # Run your phase application logic
            self.apply_phase_new()

            # Thorlabs measurements (use only the first two devices)
            thorlabs_values = [0.0, 0.0]
            if self.thorlabs:
                devices = self.thorlabs if isinstance(self.thorlabs, list) else [self.thorlabs]
                for i in range(2):
                    try:
                        thorlabs_values[i] = devices[i].read_power(unit=self.selected_unit)
                    except Exception as e:
                        print(f"Error reading Thorlabs {i}: {e}")
                        thorlabs_values[i] = 0.0

            # Record results with timestamp
            current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = [current_timestamp, index+1, thorlabs_values[0], thorlabs_values[1]]
            results.append(row)

            # Print current values
            print(f"Step {index+1} measurements:")
            print(f"  Thorlabs 1: {thorlabs_values[0]:.3f} {self.selected_unit}")
            print(f"  Thorlabs 2: {thorlabs_values[1]:.3f} {self.selected_unit}")

            # Schedule the next path after the delay
            self.after(int(delay * 1000), lambda: run_next(index + 1))

        try:
            run_next(0)
        except Exception as e:
            print(f"Experiment failed: {e}")
            import traceback
            traceback.print_exc()


    def _start_status_updates(self):
        """Start periodic status updates"""
        self._update_system_status()
        self.after(10000, self._start_status_updates)

    def _update_system_status(self):
        """Update both status and error displays"""
        try:
            self._capture_output(self.qontrol.show_errors, self.error_display)
            self._capture_output(self.qontrol.show_status, self.status_display)
        except Exception as e:
            self._show_error(f"Status update failed: {str(e)}")
            
    def _capture_output(self, device_func, display):
        """Capture output from device functions"""
        with io.StringIO() as buffer:
            with redirect_stdout(buffer):
                try:
                    device_func()
                except Exception as e:
                    print(f"Error: {str(e)}")
            output = buffer.getvalue()
            
            display.configure(state="normal")
            display.delete("1.0", "end")
            display.insert("1.0", output)
            display.configure(state="disabled")

    def _setup_event_bindings(self):
        """One-time event binding setup"""
        self.custom_grid.bind("<<SelectionUpdated>>", self._event_update_handler)
        self.custom_grid.bind("<<SelectionUpdated>>", self._get_current_channels)

    def _event_update_handler(self, event=None):
        """Handle event-driven updates"""
        current = AppData.get_last_selection()
        print(f"Current selection: {current['cross']}-{current['arm']}")
        # print(self.custom_grid.export_paths_json())
        # print(f"Live selection: {current['cross']}-{current['arm']}")
        # modes = self.get_cross_modes()  # self refers to Example instance
        # for cross_label, mode in modes.items():
        #     print(f"{cross_label}: {mode}")


    def _create_status_displays(self):
        """Status displays are now integrated in control panel"""
        pass

    # def build_grid(self, grid_size):
    #     """Initialize the grid display"""
    #     try:
    #         n = int(grid_size.split('x')[0])
    #     except:
    #         n = 8
            
    #     if hasattr(self, 'custom_grid'):
    #         self.custom_grid.destroy()
            
    #     self.custom_grid = grid.Example(
    #         self.grid_container, 
    #         grid_n=n,
    #         scale=0.8 if n >= 12 else 1.0
    #     )
    #     self.custom_grid.pack(fill="both", expand=True)
    #     self._attach_grid_listeners()

    def _initialize_live_graph(self):
        # Create figure, axes, and styling as usual
        self.figure = Figure(figsize=(3,3), dpi=100)
        self.ax = self.figure.add_subplot(111)

        # Dark background
        self.figure.patch.set_facecolor('#2b2b2b')
        self.ax.set_facecolor('#363636')
        #self.ax.set_title("Live Power Readings", color='white', fontsize=12)
        self.ax.set_xlabel("Time (s)", color='white', fontsize=10)
        self.ax.set_ylabel(f"Power ({self.selected_unit})", color='white', fontsize=10)
        self.ax.tick_params(colors='white', which='both')
        for spine in self.ax.spines.values():
            spine.set_color('white')
        self.ax.grid(True, color='gray', linestyle='--', linewidth=0.5)

        # Embed the canvas
        self.canvas = FigureCanvasTkAgg(self.figure, self.live_graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # set a manual margin so it won't shift as labels change. ---
        # (Adjust left=0.12 or 0.15 if your Y‐axis labels get cut off or cause a shift.)
        self.figure.subplots_adjust(left=0.15, right=0.85, top=0.85, bottom=0.15)

        # Draw once so it’s “centered” from the start
        self.canvas.draw()

        # Initialize data arrays
        self.live_data = []
        self.time_data = []
        self.start_time = time.time()
        self.is_live_updating = False

    def label_lines_inline(self, ax, lines, offset=0.3):
        """
        Place text labels next to the last point of each line,
        matching the line’s color, inside the graph area..
        """
        for label, line in lines:
            x_data = line.get_xdata()
            y_data = line.get_ydata()
            if len(x_data) == 0:
                continue  # Skip if there is no data

            # Get the last data point
            x_pos = x_data[-1]
            y_pos = y_data[-1]

            # Adjust the position to keep the label inside the graph
            x_offset = -0.5  # Move slightly left of the last point
            y_offset = 0.0   # Align vertically with the line

            # Add the label inside the graph
            ax.text(
                x_pos + x_offset,
                y_pos + y_offset,
                label,
                color=line.get_color(),
                va='bottom',
                ha='right',  # Align text to the right
                fontsize=7
            )

    def _update_live_graph(self):
        if not self.is_live_updating:
            return

        try:
            channels = self.daq.list_ai_channels()  # e.g. ['ai0','ai1','ai2','ai3','ai4','ai5','ai6','ai7']
            readings = self.daq.read_power(channels=channels, samples_per_channel=10, unit=self.selected_unit)
            
            # Time axis
            current_time = time.time() - self.start_time
            self.time_data.append(current_time)
            if len(self.time_data) > 100:
                self.time_data.pop(0)

            # Update / trim each channel’s data
            for i, ch_name in enumerate(channels):
                if ch_name not in self.channel_data:
                    self.channel_data[ch_name] = []
                self.channel_data[ch_name].append(readings[i])
                if len(self.channel_data[ch_name]) > 100:
                    self.channel_data[ch_name].pop(0)

            # Clear the axes
            self.ax.clear()
            self.ax.set_facecolor('#363636')
            self.ax.grid(True, color='gray', linestyle='--', linewidth=0.5)

            # Build a lines list for inline labeling
            lines = []

            # For each pinned index in AppData.selected_output_pins
            for pin_idx in AppData.selected_output_pins:
                # Make sure it's valid
                if 0 <= pin_idx < len(channels):
                    ch_name = channels[pin_idx]
                    # Plot that channel
                    line, = self.ax.plot(self.time_data,
                                        self.channel_data[ch_name],
                                        linewidth=1.5)
                    lines.append((ch_name, line))

            # Inline labeling for each line
            self.label_lines_inline(self.ax, lines, offset=0.3)

            # Reapply labels/styling
            self.ax.set_xlabel("Time (s)", color='white', fontsize=10)
            self.ax.set_ylabel(f"Power ({self.selected_unit})", color='white', fontsize=10)
            self.ax.tick_params(colors='white', which='both')
            for spine in self.ax.spines.values():
                spine.set_color('white')

            self.canvas.draw()

        except Exception as e:
            print(f"Error updating live graph: {e}")

        self.after(1000, self._update_live_graph)

    def _start_live_graph(self):
        """Start live graph updates."""
        if not self.is_live_updating:
            self.is_live_updating = True
            self.start_time = time.time()
            self.time_data = []
            self.channel_data = {} #  dict for channel data
            self._update_live_graph()

    def _stop_live_graph(self):
        """Stop live graph updates."""
        self.is_live_updating = False

    def _toggle_live_graph(self):
        """Toggle live graph updates on/off."""
        if self.is_live_updating:
            self._stop_live_graph()
        else:
            self._start_live_graph()

    def _export_live_graph(self):
        """Export the current live graph as an image file."""
        try:
            # Ask the user for the file location and name
            file_path = filedialog.asksaveasfilename(
                title="Save Live Graph",
                defaultextension=".png",
                filetypes=(("PNG files", "*.png"), ("All files", "*.*"))
            )
            if not file_path:
                return  # User canceled the save dialog

            # Save the current figure
            self.figure.savefig(file_path, format="png", dpi=300, bbox_inches="tight")
            print(f"Live graph exported to {file_path}")
        except Exception as e:
            print(f"Error exporting live graph: {e}")

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

    def _read_thorlabs_powers(self):
        """Read optical power from connected Thorlabs device(s)"""
        if not self.thorlabs:
            self._thorlabs_last_result = "No Thorlabs device found."
            return

        readings = []
        devices = self.thorlabs if isinstance(self.thorlabs, list) else [self.thorlabs]

        for i, device in enumerate(devices):
            try:
                power = device.read_power(unit=self.selected_unit)
                readings.append(f"Thorlabs {i} -> {power} {self.selected_unit}")
            except Exception as e:
                readings.append(f"Thorlabs {i}: Error - {e}")

        self._thorlabs_last_result = "\n".join(readings)

    def _update_selected_unit(self, selected_unit):
        """Update the selected unit for power measurement and refresh the live graph."""
        self.selected_unit = selected_unit  # Update the selected unit

        # Define conversion factors
        conversion_factors = {
            "uW": 1,          # MicroWatts (default)
            "mW": 1e-3,       # MilliWatts
            "W": 1e-6         # Watts
        }

        # Get the conversion factor for the selected unit
        conversion_factor = conversion_factors.get(self.selected_unit, 1)

        # Update the Y-axis label to reflect the new unit
        self.ax.set_ylabel(f"Power ({self.selected_unit})", color='white', fontsize=10)

        # Convert the data to the new unit
        for channel in self.channel_data:
            self.channel_data[channel] = [
                value * conversion_factor for value in self.channel_data[channel]
            ]

        # Re-draw the live graph with the updated unit
        if self.is_live_updating:
            self._update_live_graph()
        else:
            # Clear the graph if live updating is not active
            self.ax.clear()
            self.ax.set_facecolor('#363636')
            self.ax.grid(True, color='gray', linestyle='--', linewidth=0.5)
            self.ax.set_xlabel("Time (s)", color='white', fontsize=10)
            self.ax.set_ylabel(f"Power ({self.selected_unit})", color='white', fontsize=10)
            self.ax.tick_params(colors='white', which='both')
            for spine in self.ax.spines.values():
                spine.set_color('white')

            # Re-plot the converted data
            for channel, data in self.channel_data.items():
                self.ax.plot(self.time_data, data, label=channel, linewidth=1.5)

            self.canvas.draw()

    def _update_measurement_text(self, text):
        """Update the measurement text box with the provided text."""
        self.measurement_text_box.configure(state="normal")  # Enable editing
        self.measurement_text_box.delete("1.0", "end")  # Clear existing text
        self.measurement_text_box.insert("1.0", text)  # Insert new text
        self.measurement_text_box.configure(state="disabled")  # Disable editing


    def _read_all_measurements(self):
        """
        Unified method that reads DAQ first, then Thorlabs,
        and combines both results into the shared textbox.
        """
        self._daq_last_result = ""
        self._thorlabs_last_result = ""

        # Add a timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Read DAQ channels
        self._read_all_daq_channels()

        # Read Thorlabs devices
        self._read_thorlabs_powers()

        # Format the DAQ readings with the timestamp aligned to the right
        daq_header = f"DAQ Readings:{' ' * (95 - len('DAQ Readings:'))}{timestamp}"

        # Combine results with the formatted DAQ header
        combined = (
            daq_header + "\n" +
            self._daq_last_result +
            "\n\nThorlabs Readings:\n" + self._thorlabs_last_result
        )
        self._update_measurement_text(combined)

    def build_grid(self, grid_size):
        """Initialize the grid display with default JSON"""
        try:
            n = int(grid_size.split('x')[0])
        except:
            n = 8
            
        if hasattr(self, 'custom_grid'):
            self.custom_grid.destroy()
            
        self.custom_grid = grid.Example(
            self.grid_container, 
            grid_n=n,
            scale=0.8 if n >= 12 else 1.0
        )
        self.custom_grid.pack(fill="both", expand=True)
        self._attach_grid_listeners()
        
        # Load default JSON configuration
        # default_json = json.dumps({
        #     "A1": {"arms": ["TL", "TR", "BL", "BR"], "theta": "0", "phi": "0"},
        #     "B1": {"arms": ["TL", "TR", "BL", "BR"], "theta": "0", "phi": "0"},
        #     # ... add other default grid values
        # })

        default_json = json.dumps(AppData.default_json_grid)

        try:
            self.custom_grid.import_paths_json(default_json)
        except Exception as e:
            print(f"Error loading default grid: {str(e)}")


    def _attach_grid_listeners(self):
        """Attach event listeners to grid inputs"""
        self.grid_container.bind("<<SelectionUpdated>>", self._handle_selection_update)

        if hasattr(self.custom_grid, 'input_boxes'):
            for widgets in self.custom_grid.input_boxes.values():
                for entry in [widgets['theta_entry'], widgets['phi_entry']]:
                    entry.bind("<KeyRelease>", lambda e: self._update_device())

## config has the current values so the apply phase has to read from default_json_grid which return values in 3.14 which means 1 pi and calculate the phases for the entire grid one by one
#  and then export the calculated values in the same format as custom_grid.export_paths_json()
## calculated values 
## to config 

## how it works is that the apply phase button will read the default_json_grid which return values in terms of pi as 3.14 meaning 1 pi and calculate the phases for the entire grid using the apply_phase function and then export the calculated values in the same format as custom_grid.export_paths_json()

    def _update_device(self):
        """Update Qontrol device with current values"""
        try:
            config = self.custom_grid.export_paths_json()
            apply_grid_mapping(self.qontrol, config, self.grid_size)
        except Exception as e:
            self._show_error(f"Device update failed: {str(e)}")

    # def _update_device(self):
    #     """Update Qontrol device with current values"""
    #     try:
    #         # Check if we have a phase grid config, otherwise use the regular export
    #         if hasattr(self, 'phase_grid_config'):
    #             config = self.phase_grid_config
    #         else:
    #             config = json.loads(self.custom_grid.export_paths_json())
                
    #         apply_grid_mapping(self.qontrol, config, self.grid_size)
    #     except Exception as e:
    #         self._show_error(f"Device update failed: {str(e)}")


    def _export_config(self):
        """Export current configuration to a JSON file."""
        try:
            config_str = self.custom_grid.export_paths_json()
            # Ask the user for a file location to save the JSON configuration.
            file_path = filedialog.asksaveasfilename(
                title="Export Config",
                defaultextension=".json",
                filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
            )
            if file_path:
                with open(file_path, "w") as f:
                    f.write(config_str)
                print(f"Configuration exported to {file_path}")
        except Exception as e:
            self._show_error(f"Export failed: {str(e)}")

    def _import_config(self):
        """Import configuration from a JSON file."""
        # Open a file dialog to select a JSON file.
        file_path = filedialog.askopenfilename(
            title="Import Config",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
        )
        if file_path:
            try:
                with open(file_path, "r") as f:
                    json_str = f.read()
                self.custom_grid.import_paths_json(json_str)
                self._update_device()
                print(f"Configuration imported from {file_path}")
            except Exception as e:
                self._show_error(f"Invalid config: {str(e)}")


    def _handle_selection_update(self, event):
        """Event-driven update handler"""
        print(AppData.default_json_grid)
        # current = AppData.get_last_selection()
        # print(f"Current selection: {current['cross']}-{current['arm']}")
        # Add any UI updates here

    def update_grid(self, new_grid_size):
        cover = ctk.CTkFrame(self.grid_container, fg_color="grey16", border_width=0)
        cover.place(relwidth=1, relheight=1)
        self.grid_container.update_idletasks()
        for widget in self.grid_container.winfo_children():
            widget.destroy()
        self.build_grid(new_grid_size)
        cover.destroy()

    def _clear_grid(self):
        """Clear all selections and reset the grid, setting all values to zero"""
        try:
            # Clear all selections.
            for path in self.custom_grid.paths:
                if path.line_id in self.custom_grid.selected_paths:
                    self.custom_grid.canvas.itemconfig(path.line_id, fill="white")
            self.custom_grid.selected_paths.clear()
            
            # Clear all input boxes.
            for cross_label in list(self.custom_grid.input_boxes.keys()):
                self.custom_grid.delete_input_boxes(cross_label)
            
            # Reset cross_selected_count.
            self.custom_grid.cross_selected_count.clear()

            # Reset last selection.
            self.custom_grid.last_selection = {"cross": None, "arm": None}
            AppData.update_last_selection(None, None)
            
            # Update the selection display.
            self.custom_grid.update_selection()
            
            # Trigger the selection updated event.
            self.custom_grid.event_generate("<<SelectionUpdated>>")
            
            # Create a zero-value configuration for all crosspoints.
            zero_config = self._create_zero_config()
            
            # Apply the zero configuration to the device.
            apply_grid_mapping(self.qontrol, zero_config, self.grid_size)
            print("Grid cleared and all values set to zero")
            self._capture_output(self.qontrol.show_status, self.status_display)

        except Exception as e:
            self._show_error(f"Failed to clear grid: {str(e)}")
            print(f"Error in clear grid: {e}")

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

    def _apply_config(self):
        """Force apply current configuration"""
        self._update_device()
        self._capture_output(self.qontrol.show_status, self.status_display)

    def apply_phase_new(self):
        """
        Apply phase settings to the entire grid based on phase calibration data.
        Processes all theta and phi values in the current grid configuration.
        """
        try:
            # Get current grid configuration
            grid_config = json.loads(self.custom_grid.export_paths_json())
            if not grid_config:
                self._show_error("No grid configuration found")
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

                # Retrieve theta_ch and phi_ch from the label map
                theta_ch, phi_ch = label_map.get(cross_label, (None, None))

                # Handle interpolation for theta
                if self.interpolation_enabled and cross_label in self.interpolated_theta:
                    theta_val = self.interpolated_theta[cross_label]
                else:
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
                            phase_grid_config[cross_label]["theta"] = str(current_theta)  # Store in mA
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
                            phase_grid_config[cross_label]["phi"] = str(current_phi)  # Store in mA
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

            # Update the mapping display with detailed results
            self.mapping_display.configure(state="normal")
            self.mapping_display.delete("1.0", "end")
            self.mapping_display.insert("1.0", "Phase Application Results:\n\n")
            self.mapping_display.insert("end", "Successfully applied:\n")
            for channel in applied_channels:
                self.mapping_display.insert("end", f"• {channel}\n")
            if failed_channels:
                self.mapping_display.insert("end", "\nFailed to apply:\n")
                for channel in failed_channels:
                    self.mapping_display.insert("end", f"• {channel}\n")
            self.mapping_display.configure(state="disabled")

            print(phase_grid_config)
            self._capture_output(self.qontrol.show_status, self.status_display)

            try:
                # Apply the updated configuration to the device
                config_json = json.dumps(phase_grid_config)
                apply_grid_mapping(self.qontrol, config_json, self.grid_size)
            except Exception as e:
                self._show_error(f"Device update failed: {str(e)}")

        except Exception as e:
            self._show_error(f"Failed to apply phases: {str(e)}")
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
        c = params['phase']     # offset phase in radians
        d = params['offset']
        
        '''
        # Find the positive phase the heater must add 
        delta_phase = (phase_value % 2) * np.pi;

        # Calculate the heating power for this phase shift
        P = delta_phase / b;
        '''
        
        # Check if phase is within valid range
        if phase_value < c/np.pi:
            print(f"Warning: Phase {phase_value}π is less than offset phase {c/np.pi}π for channel {channel}")
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

    def _show_full_status(self):
        """Display detailed device status"""
        self._capture_output(self.qontrol.show_status, self.status_display)

    def _show_error(self, message):
        """Display error message in compact dialog"""
        self.error_display.configure(state="normal")
        self.error_display.delete("1.0", "end")
        self.error_display.insert("1.0", message)
        self.error_display.configure(state="disabled")
        
        # Compact error dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Error")
        dialog.geometry("300x80")  # Smaller dialog
        
        ctk.CTkLabel(dialog, text=message, wraplength=280).pack(pady=5)
        ctk.CTkButton(dialog, text="OK", command=dialog.destroy, width=60).pack(pady=5)

    def update_grid_size(self, new_size):
        """Handle grid size changes"""
        self.grid_size = new_size
        self.build_grid(new_size)

    def _get_current_channels(self, event=None):
        """Get theta/phi channels for current selection"""
        current = AppData.get_last_selection()
        if not current or 'cross' not in current:
            return None, None
        
        label_map = create_label_mapping(8)
        theta_ch, phi_ch = label_map.get(current['cross'], (None, None))
        # print(f"θ{theta_ch}, φ{phi_ch}")
        print(f"Current selection: {current['cross']}-{current['arm']}")

        return theta_ch, phi_ch

    def _run_resistance_calibration(self):
        """Run resistance characterization on selected channel"""
        try:
            theta_ch, phi_ch = self._get_current_channels()
            channel_type = self.phase_selector.radio_var.get()
            # channel_type = "theta"
            target_channel = theta_ch if channel_type == "theta" else phi_ch
            
            if target_channel is None:
                raise ValueError("No valid channel selected")
                
            # Run characterization
            self._characterize_resistance(target_channel)
            
            # Update UI
            self._update_calibration_display_R(target_channel)
            
        except Exception as e:
            self._show_error(f"Calibration failed: {str(e)}")

    def _characterize_resistance(self, channel):
        """Execute characterization routine with linear+cubic fit analysis"""
        # Measurement setup
        start_current = 0
        end_current = self.qontrol.globalcurrrentlimit
        steps = 10
        delay = 0.05 ## Delay between current steps in seconds change this back to 0.5
        currents = np.linspace(start_current, end_current, steps).astype(float)
        voltages = []

        # Current sweep measurement
        for I in currents:
            self.qontrol.set_current(channel, float(I))
            time.sleep(delay)
            voltages.append(float(self.qontrol.device.v[channel]))
        
        # Reset current to zero
        self.qontrol.set_current(channel, 0.0)

        # Cubic+linear fit
        X = np.vstack([currents**3, currents, np.ones_like(currents)]).T
        coefficients, residuals, _, _ = np.linalg.lstsq(X, voltages, rcond=None)
        a, c, d = coefficients

        resistance = a * currents**2 + c  # Modified from derivative-based calculation

        # Calculate additional parameters
        rmin = np.min(resistance)
        rmax = np.max(resistance)
        alpha = a / c if c != 0 else float('inf')

        # Store comprehensive results
        self.resistance_params[channel] = {
            'a': a,
            'c': c,
            'd': d,
            'resistances': resistance.tolist(),
            'rmin': float(rmin),
            'rmax': float(rmax),
            'alpha': float(alpha),
            'currents': currents.tolist(),
            'voltages': voltages,
            'max_current': float(end_current),
            'resistance_parameters': [float(a), float(c), float(d)]
        }

        # Enhanced print output
        print(f"\nChannel {channel} Characterization (Cubic+Linear Model)")
        print(f"a = {a:.2e}, c = {c:.2e}, d = {d:.2e}")
        # print(f"Resistance: {resistance}")
        # print(f"V(I) = {a:.2e}·I³ + {c:.2e}·I + {d:.2e}")
        # print(f"Max Current: {end_current:.1f} mA")
        print(f"Average Resistance: {np.mean(resistance):.2f}Ω")
   
    def _update_calibration_display_R(self, channel):
        """Update UI with calibration results"""
        params = self.resistance_params.get(channel)
        if not params:
            return
        
        # Get current channel type from radio buttons
        channel_type = self.phase_selector.radio_var.get()
        # channel_type = "theta"
        
        # Generate plot with channel context
        fig = self._create_calibration_plot_R(params, channel_type, channel)  # Add missing args
        self._display_plot_R(fig, channel)


    def _create_calibration_plot_R(self, params, channel_type, target_channel):
        """Generate styled resistance characterization plot"""
        current = AppData.get_last_selection()
        label_map = create_label_mapping(8)
        channel_type = self.phase_selector.radio_var.get()
        # channel_type = "theta"
        channel_symbol = "θ" if channel_type == "theta" else "φ"

        # Get both channels but only show selected one
        theta_ch, phi_ch = label_map.get(current['cross'], (None, None))
        
        # Create plot with dark theme
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#363636')
        
        # Plot data points and fit curve
        ax.plot(params['currents'], params['voltages'], 
            'o', color='white', label='Measured Data')
        x_fit = np.linspace(min(params['currents']), max(params['currents']), 100)
        y_fit = params['a']*x_fit**3 + params['c']*x_fit + params['d']
        ax.plot(x_fit, y_fit, color='#ff4b4b', linewidth=1, label='Cubic Fit')
        #ax.plot(x_fit, y_fit, label='Cubic Fit')

        # # Dynamic title based on selected channel type
        # title_str = (f"Resistance Characterization: {current['cross']} "
        #             f"Characterizing {channel_type.capitalize()} Channel: {target_channel}")
        title_str = (f"Resistance Characterization of {current['cross']}:{channel_symbol} at Channel {target_channel}")

        ax.set_title(title_str, color='white', fontsize=12)
        ax.set_xlabel("Current (mA)", color='white', fontsize=10)
        ax.set_ylabel("Voltage (V)", color='white', fontsize=10)
        
        # Configure ticks and borders
        ax.tick_params(colors='white', which='both')
        for spine in ax.spines.values():
            spine.set_color('white')
            
        # Legend styling
        legend = ax.legend(frameon=True, facecolor='#2b2b2b', edgecolor='white')
        for text in legend.get_texts():
            text.set_color('white')

        #ax.legend()

        fig.tight_layout()        
        return fig

    def _display_plot_R(self, fig, channel):
        """Display matplotlib plot in a popup window and graph tab"""
   
        # Convert plot to image with tight borders
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img = Image.open(buf)
        fig.tight_layout()

        ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(480, 320))

        
        self.graph_image_label1.configure(image=ctk_image, text="")
        self._current_image_ref1 = ctk_image

        plt.close(fig)

                ## Phase Calibration
    def _run_phase_calibration(self):
        """Run phase characterization on the selected channel."""
        try:
            # Retrieve the current selection from AppData
            current = AppData.get_last_selection()
            if not current or 'cross' not in current:
                raise ValueError("No valid cross selection found.")
            
            cross_label = current['cross']
            
            # Create a label mapping (assuming an 8x8 grid)
            label_map = create_label_mapping(8)
            theta_ch, phi_ch = label_map.get(cross_label, (None, None))
            print(f"θ{theta_ch}, φ{phi_ch}")
            
            if theta_ch is None or phi_ch is None:
                raise ValueError(f"No valid channels found for cross label: {cross_label}")
            
            # Get the phase shifter selection from the widget ("theta" or "phi")
            channel_type = self.phase_selector.radio_var.get()
            target_channel = theta_ch if channel_type == "theta" else phi_ch
            
            if target_channel is None:
                raise ValueError("No valid channel selected.")
            
            # Instead of using target_channel to fetch the mode,
            # use cross_label (since AppData.io_config is keyed by cross label, e.g. "A1")
            if cross_label not in AppData.io_config:
                available_keys = list(AppData.io_config.keys())
                raise ValueError(f"Cross label {cross_label} is not in io_config! Available keys: {available_keys}")
            
            mode = AppData.io_config[cross_label]
            print(f"Running phase calibration for channel {target_channel} (mode: {mode})")
            
            # Run the calibration logic using the numeric target channel and the mode
            self._characterize_phase(target_channel, mode)
            
            # Update the UI with calibration results
            self._update_calibration_display_P(target_channel, mode)
            
        except Exception as e:
            self._show_error(f"Calibration failed: {str(e)}")

    def _characterize_phase(self, channel, io_config):
        """Execute phase characterization routine"""
        # Measurement parameters
        start_current = 0
        end_current = self.qontrol.globalcurrrentlimit
        steps = 10
        delay = 0.5
        
        currents = np.linspace(start_current, end_current, steps)
        optical_powers = []
        
        # Current sweep measurement
        for I in currents:
            self.qontrol.set_current(channel, float(I))
            time.sleep(delay)
            optical_powers.append(self.thorlabs[0].read_power()) # Read power from 1st Thorlabs device
        
        # Reset current to zero
        self.qontrol.set_current(channel, 0.0)

        # Perform cosine fit
        if io_config == "cross":
            fit_result = self.fit_cos(currents, optical_powers)
        else:
            fit_result = self.fit_cos_negative(currents, optical_powers)

        # Store phase parameters
        self.phase_params[channel] = {
            'io_config': io_config,
            'amp': fit_result['amp'],
            'omega': fit_result['omega'],
            'phase': fit_result['phase'],
            'offset': fit_result['offset'],
            'currents': currents.tolist(),
            'optical_powers': optical_powers
        }

        print(f"Channel {channel} ({io_config}) Phase Characterization Complete")
        print(f"Amp: {fit_result['amp']:.2e} mW")
        print(f"Frequency: {fit_result['freq']:.2f} Hz")
        print(f"Phase: {fit_result['phase']:.2f} rad")
        

    def fit_cos(self, xdata, ydata):
        """Positive cosine fit"""
        print("Fitting positive cosine...")
        guess_freq = 1/20
        guess_amp = np.std(ydata) * 2.**0.5
        guess_offset = np.mean(ydata)
        guess = [guess_amp, 2.*np.pi*guess_freq, 0., guess_offset]
        
        def cos_func(P, A, b, c, d):
            return A * np.cos(b*P + c) + d

        popt, pcov = optimize.curve_fit(
            cos_func, xdata, ydata, p0=guess,
            bounds=([0, 0, -np.pi, -np.inf], [np.inf, np.inf, np.pi, np.inf])
        )

        A, b, c, d = popt
        return self._create_fit_result(A, b, c, d, cos_func, popt, pcov, guess)  # Pass pcov

    def fit_cos_negative(self, xdata, ydata):
        """Negative cosine fit"""
        print("Fitting negative cosine...")
        guess_freq = 1/20
        guess_amp = np.std(ydata) * 2.**0.5
        guess_offset = np.mean(ydata)
        guess = [guess_amp, 2.*np.pi*guess_freq, 0., guess_offset]

        def cos_func(P, A, b, c, d):
            return -A * np.cos(b*P + c) + d

        popt, pcov = optimize.curve_fit(
            cos_func, xdata, ydata, p0=guess,
            bounds=([0, 0, -np.pi, -np.inf], [np.inf, np.inf, np.pi, np.inf])
        )

        A, b, c, d = popt
        return self._create_fit_result(A, b, c, d, cos_func, popt, pcov, guess)  # Pass pcov
    
    def _create_fit_result(self, A, b, c, d, cos_func, popt, pcov, guess):
        """Package fit results consistently"""
        print("Creating fit result...")
        return {
            'amp': A,
            'omega': b,
            'phase': c,
            'offset': d,
            'freq': b/(2.*np.pi),
            'period': 1/(b/(2.*np.pi)),
            'fitfunc': cos_func,
            'maxcov': np.max(pcov),
            'rawres': (guess, popt, pcov)
        }
    
    def _create_calibration_plot_P(self, params, channel_type, target_channel, io_config):
        """Generate phase calibration plot"""
        print("Creating calibration plot...")
        current = AppData.get_last_selection()
        channel_symbol = "θ" if channel_type == "theta" else "φ"
        
        # Create plot with dark theme
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#363636')
        
        # Plot data
        ax.plot(params['currents'], params['optical_powers'], 
            'o', color='white', label='Measured Data')
        
        # Plot fit - recreate the cosine function based on io_config
        x_fit = np.linspace(min(params['currents']), max(params['currents']), 100)
        
        # Define the cosine function based on io_config
        if io_config == "cross":
            y_fit = params['amp'] * np.cos(params['omega']*x_fit + params['phase']) + params['offset']
        else:  # bar
            y_fit = -params['amp'] * np.cos(params['omega']*x_fit + params['phase']) + params['offset']
            
        ax.plot(x_fit, y_fit, color='#ff4b4b', linewidth=1, label='Cosine Fit')

        # Labels and titles
        title_str = f"Phase Characterization of {current['cross']}:{channel_symbol} at Channel {target_channel} ({io_config.capitalize()})"
        ax.set_title(title_str, color='white', fontsize=12)
        ax.set_xlabel("Current (mA)", color='white', fontsize=10)
        ax.set_ylabel("Optical Power (mW)", color='white', fontsize=10)
        
        # Configure ticks and borders
        ax.tick_params(colors='white', which='both')
        for spine in ax.spines.values():
            spine.set_color('white')
            
        # Legend styling
        legend = ax.legend(frameon=True, facecolor='#2b2b2b', edgecolor='white')
        for text in legend.get_texts():
            text.set_color('white')

        return fig

    def _update_calibration_display_P(self, channel, io_config):
        """Update UI with calibration results"""
        print("Updating calibration display...")
        # Change this line to use self.phase_params instead of self.calibration_params
        params = self.phase_params.get(channel)
        print(params)
        if not params:
            return
            
        # Get current channel type
        channel_type = self.phase_selector.radio_var.get()
        # channel_type="theta"
        # Generate and display plot
        fig = self._create_calibration_plot_P(params, channel_type, channel, io_config)
        self._display_plot_P(fig, channel)
        print("Updated calibration display")

    def _display_plot_P(self, fig, channel):
        """Display matplotlib plot in a popup window"""
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img = Image.open(buf)
        fig.tight_layout()
    
        ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(480, 320))
        
        self.graph_image_label2.configure(image=ctk_image, text="")
        self._current_image_ref2 = ctk_image
        
        plt.close(fig)
    
    def _record_power(self):
        """Record and display power measurements in the tab"""
        # Get user-specified duration 
        try:
            record_time = float(self.measure_time_entry.get())
        except ValueError:
            record_time = 5.0
    
        # Load simulated data
        data = np.load("power_data_cw.npy")
        self.measured_power_data = data
    
        # Create time axis based on recording time
        time_axis = np.linspace(0, record_time, data.shape[0])
    
        # Generate and display plot
        fig = self._create_measurement_plot(time_axis, data)
        self._update_measurement_display(fig)
        
        # Save data (optional)
        save_dir = "measurements"
        os.makedirs(save_dir, exist_ok=True)
        np.savetxt(
            os.path.join(save_dir, f"measurement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"),
            data,
            header=f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nOutput1 Output2 Output3",
            comments=''
        )
        
        plt.close(fig)
            
    def _create_measurement_plot(self, time_axis, data):
        fig, ax = plt.subplots(figsize=(4, 4))
        
        fig.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#363636')
         
        ax.plot(time_axis, data[:, 0], color='red', label="Site 1")
        ax.plot(time_axis, data[:, 1], color='green', label="Site 2")
        ax.plot(time_axis, data[:, 2], color='blue', label="Site 3")
       
        ax.set_xlabel("Time (s)", color='white')
        ax.set_ylabel("Power (mW)", color='white')
        
        ax.tick_params(colors='white', which='both')
        for spine in ax.spines.values():
            spine.set_color('white')
        
        legend = ax.legend(frameon=True, facecolor='#2b2b2b', edgecolor='white')
        for text in legend.get_texts():
            text.set_color('white')
        
        fig.tight_layout()
        return fig
            
    def _update_measurement_display(self, fig):
        # Convert plot to CTKimage
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img = Image.open(buf)
            
        # Get current frame dimensions
        width = self.measure_plot_frame.winfo_width()
        height = self.measure_plot_frame.winfo_height()
        ctk_image = ctk.CTkImage(
            light_image=img,
            dark_image=img,
            size=(320, 320)
        )
            
        # Update display
        self.measure_image_label.configure(image=ctk_image, text="")
        self.measure_status_label.configure(
            text=f"Last measurement: {datetime.now().strftime('%H:%M:%S')}"
        )
            
        # Keep reference to prevent garbage collection
        self._current_measure_image = ctk_image


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

    def _on_sweep_file_changed(self, selected_file):
        """Handler to reload sweep file for interpolation"""
        try:
            self.interpolation_manager.load_sweep_file(selected_file)
            print(f"[Interpolation] Loaded file: {selected_file}")
            
            # Update UI to show file is loaded
            self.interp_plot_label.configure(text=f"File loaded: {selected_file}")
            
        except FileNotFoundError as e:
            self._show_error(f"File not found: {selected_file}")
        except Exception as e:
            self._show_error(f"Failed to load file: {e}")

    def _on_plot_interpolation(self):
        """Called when 'Plot' button is clicked in Interpolation tab."""
        if self.interp_option_a.get() != "enable":
            self._show_error("Interpolation is disabled.")
            return

        # Ensure file is loaded
        if self.interpolation_manager.current_file is None:
            self._on_sweep_file_changed(self.sweep_file_menu.get())

        try:
            angle_input = float(self.angle_entry.get())
        except ValueError:
            self._show_error("Please enter a valid number for the angle.")
            return
        except Exception as e:
            self._show_error(f"Invalid angle input: {e}")
            return

        try:
            # Create plot using interpolation manager
            import matplotlib.pyplot as plt
            from PIL import Image
            from customtkinter import CTkImage
            import io
            
            plt.close('all')
            fig = self.interpolation_manager.create_plot(angle_input)
            
            # Convert matplotlib figure to CTkImage
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=100, bbox_inches='tight')
            buf.seek(0)
            img = Image.open(buf).copy()
            buf.close()

            # Display the image
            ctk_img = CTkImage(light_image=img, dark_image=img, size=(450, 360))
            self.interp_plot_label.configure(image=ctk_img, text="")
            self._interp_img_ref = ctk_img  # Keep reference to prevent garbage collection
            
            plt.close(fig)
            
            # Get corrected angle info and display it
            angle_info = self.interpolation_manager.get_corrected_angle(angle_input * np.pi)
            status_text = f"Input: {angle_info['input_pi']:.3f}π → Output: {angle_info['output_pi']:.3f}π"
            if angle_info['interpolated']:
                status_text += " (interpolated)"
            else:
                status_text += " (no interpolation)"
            print(f"[Interpolation] {status_text}")

        except ValueError as e:
            self._show_error(str(e))
        except Exception as e:
            import traceback
            self._show_error(f"Failed to plot: {e}")
            traceback.print_exc()

    def _on_interpolation_option_changed(self, value=None):
        """Handle changes to interpolation tab options."""
        a = self.interp_option_a.get()
        b = self.interp_option_b.get()

        print(f"[Interpolation] Option A: {a}, Option B: {b}")

        # Define workflow based on (a, b)
        if a == "enable" and b == "satisfy with sweep files":
            print("→ Run workflow: Interpolation + Sweep compatibility")
            # Enable file selection and angle input
            self.sweep_file_menu.configure(state="normal")
            self.angle_entry.configure(state="normal")
            self.plot_button.configure(state="normal")
            
        elif a == "enable" and b == "Not satisfy":
            print("→ Run workflow: Interpolation only")
            # Enable controls
            self.sweep_file_menu.configure(state="normal")
            self.angle_entry.configure(state="normal")
            self.plot_button.configure(state="normal")
            
        elif a == "disable":
            print("→ Interpolation disabled")
            # Disable controls
            self.sweep_file_menu.configure(state="disabled")
            self.angle_entry.configure(state="disabled")
            self.plot_button.configure(state="disabled")
            self.interp_plot_label.configure(image=None, text="No plot available.")
            
    def apply_phase_with_interpolation(self, phase_value: float, channel: int) -> float:
        """
        Apply interpolation to phase value if enabled.
        
        Args:
            phase_value: Original phase value in radians
            channel: Channel number
            
        Returns:
            Corrected phase value if interpolation is enabled, otherwise original value
        """
        if self.interp_option_a.get() == "enable" and self.interpolation_manager.current_file:
            try:
                corrected, interpolated = self.interpolation_manager.theta_trans(phase_value)
                print(f"[Interpolation] Channel {channel}: {phase_value/np.pi:.3f}π → {corrected/np.pi:.3f}π")
                return corrected
            except Exception as e:
                print(f"[Interpolation] Error for channel {channel}: {e}")
                return phase_value
        else:
            return phase_value

    # def apply_phase_sweep(self):
    #     """
    #     Apply phase settings to the entire grid based on phase calibration data.
    #     Processes all theta and phi values in the current grid configuration.
    #     """
    #     try:
    #         # Get current grid configuration
    #         grid_config = AppData.default_json_grid
    #         print(grid_config)
    #         if not grid_config:
    #             print("No grid configuration found")
    #             return
                
    #         # Create label mapping for channel assignments
    #         label_map = create_label_mapping(8)  # Assuming 8x8 grid
            
    #         # Create a new configuration with current values
    #         phase_grid_config = copy.deepcopy(grid_config)
            
    #         # Track successful and failed applications
    #         applied_channels = []
    #         failed_channels = []
            
    #         # Process each cross in the grid
    #         for cross_label, data in grid_config.items():
    #             # Skip if this cross isn't in our mapping
    #             if cross_label not in label_map:
    #                 continue
                    
    #             theta_ch, phi_ch = label_map[cross_label]
    #             theta_val = data.get("theta", "0")
    #             phi_val = data.get("phi", "0")

    #             # Process theta channel
    #             if theta_ch is not None and theta_val:
    #                 try:
    #                     theta_float = float(theta_val)
    #                     current_theta = self._calculate_current_for_phase(theta_ch, theta_float, "cross", "bar")
    #                     if current_theta is not None:
    #                         # Quantize to 5 decimal places
    #                         current_theta = round(current_theta, 5)
    #                         # Update the phase_grid_config with current value
    #                         phase_grid_config[cross_label]["theta"] = str(current_theta)  # Store in A
    #                         applied_channels.append(f"{cross_label}:θ = {current_theta:.5f} mA")
    #                     else:
    #                         failed_channels.append(f"{cross_label}:θ (no calibration)")
    #                 except Exception as e:
    #                     failed_channels.append(f"{cross_label}:θ ({str(e)})")

    #             # Process phi channel
    #             if phi_ch is not None and phi_val:
    #                 try:
    #                     phi_float = float(phi_val)
    #                     current_phi = self._calculate_current_for_phase(phi_ch, phi_float, "cross", "bar")
    #                     if current_phi is not None:
    #                         # Quantize to 5 decimal places
    #                         current_phi = round(current_phi, 5)
    #                         # Update the phase_grid_config with current value
    #                         phase_grid_config[cross_label]["phi"] = str(current_phi)  # Store in A
    #                         applied_channels.append(f"{cross_label}:φ = {current_phi:.5f} mA")
    #                     else:
    #                         failed_channels.append(f"{cross_label}:φ (no calibration)")
    #                 except Exception as e:
    #                     failed_channels.append(f"{cross_label}:φ ({str(e)})")
            
    #         # Store the phase grid config for later use
    #         self.phase_grid_config = phase_grid_config
            
    #         # Only show error message if there are failures
    #         if failed_channels:
    #             result_message = f"Failed to apply to {len(failed_channels)} channels"
    #             print(result_message)
    #             print("Failed channels:", failed_channels)
                
    #         # Debugging: Print the grid size
    #         print(f"Grid size: {self.grid_size}")
            
    #         try:
    #             config_json = json.dumps(phase_grid_config)
    #             apply_grid_mapping(self.qontrol, config_json, self.grid_size)
    #         except Exception as e:
    #             print(f"Device update failed: {str(e)}")        

    #         return phase_grid_config
            
    #     except Exception as e:
    #         print(f"Failed to apply phases: {str(e)}")
    #         import traceback
    #         traceback.print_exc()
    #         return None
