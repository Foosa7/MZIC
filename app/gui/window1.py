# app/gui/window1.py
from app.imports import *

import threading
from decimal import *
import copy
import sympy as sp
from app.utils.appdata import AppData
import io
from contextlib import redirect_stdout
from app.gui.widgets import PhaseShifterSelectionWidget
import customtkinter as ctk
from app.utils.gui import grid
from app.utils.qontrol.mapping_utils import get_mapping_functions
# from app.utils.qontrol.qmapper8x8 import create_label_mapping, apply_grid_mapping
# from app.utils.qontrol.qmapper12x12 import create_label_mapping as create_label_mapping_12x12   
from collections import defaultdict
from app.utils.calibrate.calibrate import CalibrationUtils
from app.utils.gui.plot_utils import PlotUtils
from typing import Dict, Any
from scipy import optimize
from app.utils.switch_measurements import SwitchMeasurements

class Window1Content(ctk.CTkFrame):
    ### Define the callbacks for the interpolation functionality and update the label###
    def _on_interpolate_theta_toggle(self):
        """Enable/disable interpolation and update theta values for 6 nodes."""
        self.interpolation_enabled = self.interpolate_theta_var.get()
        if self.interpolation_enabled:
            # List of 6 special nodes
            special_nodes = ["E1", "E2", "F1", "G1", "G2", "H1"]
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
                #updated.append(f"{node}: {interpolated:.3f}")
                updated.append(f"{node}: {interpolated:.4g} π \n")
            # Show updated values
            self.interpolated_theta_label.configure(text=" ".join(updated) if updated else "No valid theta found")
        else:
            self.interpolated_theta.clear()
            self.interpolated_theta_label.configure(text="")
        ######

    def __init__(self, master, channel, fit, IOconfig, app, qontrol, thorlabs, daq, switch_input, switch_output, phase_selector=None, grid_size="8x8", **kwargs):
        super().__init__(master, **kwargs)
        self.qontrol = qontrol
        self.thorlabs = thorlabs
        self.daq = daq   
        self.switch_input = switch_input 
        self.switch_output = switch_output  
        self.grid_size = grid_size
        self.after_id = None
        self.control_panel = None  
        self.resistance_params: Dict[int, Dict[str, Any]] = {}
        self.calibration_params = {'cross': {}, 'bar': {}}
        self.phase_params = {}
        self.calibration_utils = CalibrationUtils()
        self.plot_utils = PlotUtils()
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
        self._update_selection_display()
        self._setup_event_bindings()

        self.selected_unit = "mW"  # Default unit for power measurement

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
            ("Import", self.import_calibration_data),
            ("Export", self.export_calibration_data),
            ("Current", self._apply_config),
            ("Appdata", self.export_appdata_calibration),
            ("RP", self.run_rp_calibration),  # Run Resistance and Phase calibration
            ("Status", self._show_full_status),
            ("Clear", self._clear_grid),
            ("R", self.characterize_resistance),
            # ("P", self.characterize_phase),
            ("AP", self.apply_phase_new),
            ("Phase", self.apply_phase_new_json)  # Add this new button
        ]

        for col in range(len(controls)):
            btn_frame.grid_columnconfigure(col, weight=1)

        # Create buttons with adjusted styling
        for col, (text, cmd) in enumerate(controls):
            btn = ctk.CTkButton(
                btn_frame, 
                text=text,
                command=cmd,
                width=8, 
                height=16,
                # width=20, 
                # height=24,
                font=ctk.CTkFont(size=12) 
            )
            btn.grid(row=0, column=col, padx=1, sticky="nsew")

        # Label to show updated values
        self.interpolated_theta_label = ctk.CTkLabel(btn_frame, text="")
        self.interpolated_theta_label.grid(row=2, column=0, columnspan=7, sticky="ew")

        # Compact notebook for displays
        notebook = ctk.CTkTabview(inner_frame, height=180, width=300)  # Fixed height, width for the right side panel
        notebook.grid_propagate(False)
        notebook.grid(row=1, column=0, sticky="nsew", pady=(0, 0))
        inner_frame.grid_columnconfigure(0, weight=1)

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

        ### Interpolation tab ###
        interpolation_tab = notebook.add("Interpolation")
        interpolation_tab.grid_columnconfigure(0, weight=1)
        interpolation_tab.grid_columnconfigure(1, weight=2)  # Give more space to the dropdown column

        # Row 0: Enable Interpolation
        option_a_label = ctk.CTkLabel(interpolation_tab, text="Enable Interpolation:")
        option_a_label.grid(row=0, column=0, padx=(10, 5), pady=(10, 5), sticky="w")

        self.interp_option_a = ctk.CTkOptionMenu(interpolation_tab,
                                                values=["enable", "disable"],
                                                command=self._on_interpolation_option_changed)
        self.interp_option_a.set("enable")   ## Default to "enable"
        self.interp_option_a.grid(row=0, column=1, padx=(5, 10), pady=(10, 5), sticky="ew")

        # Row 1: Satisfy sweep files?
        option_b_label = ctk.CTkLabel(interpolation_tab, text="Satisfy sweep files?")
        option_b_label.grid(row=1, column=0, padx=(10, 5), pady=5, sticky="w")

        self.interp_option_b = ctk.CTkOptionMenu(interpolation_tab,
                                                values=["satisfy with sweep files", "Not satisfy"],
                                                command=self._on_interpolation_option_changed)
        self.interp_option_b.set("satisfy with sweep files")  # Default to "satisfy with sweep files"
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

        self.angle_entry = ctk.CTkEntry(interpolation_tab, placeholder_text="e.g., 1.00")
        self.angle_entry.insert(0, "1.00")  # Default to 1.00 π radians
        self.angle_entry.grid(row=4, column=1, padx=(5, 10), pady=5, sticky="ew")

        # Row 5: Plot button
        self.plot_button = ctk.CTkButton(
            interpolation_tab,
            text="Plot",
            command=self._on_plot_interpolation
        )
        self.plot_button.grid(row=5, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="ew")

        # Row 6: Interpolate Theta toggle
        self.interpolate_theta_var = ctk.BooleanVar(value=False)
        self.interpolate_theta_button = ctk.CTkCheckBox(
            interpolation_tab,
            text="Interpolate Theta (6 nodes)",
            variable=self.interpolate_theta_var,
            command=self._on_interpolate_theta_toggle
        )
        self.interpolate_theta_button.grid(row=6, column=0, columnspan=2, padx=10, pady=(5, 0), sticky="ew")

        # Row 7: Plot area
        self.interp_plot_label = ctk.CTkLabel(interpolation_tab, text="No image yet")
        self.interp_plot_label.grid(row=7, column=0, columnspan=2, padx=10, pady=(5, 10), sticky="nsew")
        interpolation_tab.grid_rowconfigure(7, weight=1)

        # Load the default file if it's available
        if default_file != "No files available":
            try:
                self.interpolation_manager.load_sweep_file(default_file)
                print(f"[Interpolation] Default file loaded: {default_file}")
                self.interp_plot_label.configure(text=f"\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n File loaded: {default_file}")
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
        
        self.sweep_steps_entry = ctk.CTkEntry(sweep_tab, placeholder_text="200")
        self.sweep_steps_entry.insert(0, "200")
        self.sweep_steps_entry.grid(row=4, column=1, padx=(5, 10), pady=5, sticky="ew")
        
        # Row 5: Dwell time
        dwell_label = ctk.CTkLabel(sweep_tab, text="Dwell time (ms):")
        dwell_label.grid(row=5, column=0, padx=(10, 5), pady=5, sticky="w")
        
        self.sweep_dwell_entry = ctk.CTkEntry(sweep_tab, placeholder_text="1e2")
        self.sweep_dwell_entry.insert(0, "1e2")  # Default to 100 ms 
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
        switch_tab = notebook.add("Switches")  
        switch_tab.grid_columnconfigure(0, weight=1)
        switch_tab.grid_columnconfigure(1, weight=1)

        # Create frames for each switch
        output_frame = ctk.CTkFrame(switch_tab)
        output_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        input_frame = ctk.CTkFrame(switch_tab)
        input_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # OUTPUT SWITCH CONTROLS
        output_header = ctk.CTkLabel(output_frame, text="Output Switch", 
                                font=("TkDefaultFont", 14, "bold"))
        output_header.pack(pady=(5, 10))

        # Buttons for output switch
        self.output_get_button = ctk.CTkButton(
            output_frame,
            text="Get Current Channel",
            command=lambda: self._get_switch_channel("output")
        )
        self.output_get_button.pack(pady=5)

        # Status label for output
        self.output_status_label = ctk.CTkLabel(
            output_frame, 
            text="Current Channel: Unknown",
            font=("TkDefaultFont", 11, "bold")
        )
        self.output_status_label.pack(pady=(10, 5))

        # OUTPUT QUICK BUTTONS
        self.output_quick_frame = ctk.CTkFrame(output_frame)
        self.output_quick_frame.pack(pady=5)
        self._build_quick_buttons(self.output_quick_frame, "output", "12x12")  # Always 12 buttons

        # INPUT SWITCH CONTROLS
        input_header = ctk.CTkLabel(input_frame, text="Input Switch", 
                                font=("TkDefaultFont", 14, "bold"))
        input_header.pack(pady=(5, 10))

        # Buttons for input switch
        self.input_get_button = ctk.CTkButton(
            input_frame,
            text="Get Current Channel",
            command=lambda: self._get_switch_channel("input")
        )
        self.input_get_button.pack(pady=5)

        # Status label for input
        self.input_status_label = ctk.CTkLabel(
            input_frame, 
            text="Current Channel: Unknown",
            font=("TkDefaultFont", 11, "bold")
        )
        self.input_status_label.pack(pady=(10, 5))

        # INPUT QUICK BUTTONS
        self.input_quick_frame = ctk.CTkFrame(input_frame)
        self.input_quick_frame.pack(pady=5)
        self._build_quick_buttons(self.input_quick_frame, "input", "12x12")  # Always 12 buttons
        # Compact error display in inner_frame
        self.error_display = ctk.CTkTextbox(inner_frame, height=100, state="disabled")
        self.error_display.grid(row=2, column=0, sticky="ew", pady=(2, 0))
    
    def _build_quick_buttons(self, parent_frame, switch_type, mesh_size=None):
        """Build quick buttons - always 12 buttons, 4 per row"""
        # Remove any existing buttons
        for widget in parent_frame.winfo_children():
            widget.destroy()
        
        # Always create 12 buttons
        for i in range(1, 13):  # 1 to 12
            row = (i - 1) // 4  # 4 buttons per row
            col = (i - 1) % 4
            btn = ctk.CTkButton(
                parent_frame,
                text=str(i),
                width=30,
                command=lambda ch=i: self._quick_set_channel(ch, switch_type)
            )
            btn.grid(row=row, column=col, padx=2, pady=2)

    def _on_measure_switch_changed(self, value):
        """Show/hide switch channel selection based on measure option"""
        if value == "Yes":
            self.switch_channels_label.grid()
            self.switch_channels_entry.grid()
        else:
            self.switch_channels_label.grid_remove()
            self.switch_channels_entry.grid_remove()

    def _parse_switch_channels(self, channel_string):
        """Parse channel string input to get list of channel numbers."""
        return SwitchMeasurements.parse_switch_channels(channel_string)

    def _get_switch_channel(self, switch_type):
        """Get the current channel from the specified switch"""
        if switch_type == "output":
            switch = self.switch_output
            status_label = self.output_status_label
        else:  # input
            switch = self.switch_input
            status_label = self.input_status_label
            
        if not switch:
            self._show_error(f"{switch_type.capitalize()} switch device not connected")
            return
            
        try:
            channel = switch.get_channel()
            if channel is not None:
                status_label.configure(
                    text=f"Current Channel: {channel}",
                    text_color="white"
                )
            else:
                status_label.configure(
                    text="Failed to read channel",
                    text_color="red"
                )
        except Exception as e:
            self._show_error(f"Failed to read channel: {e}")

    def _quick_set_channel(self, channel, switch_type):
        """Quick set channel using numbered buttons"""
        if switch_type == "output":
            switch = self.switch_output
            status_label = self.output_status_label
        else:  # input
            switch = self.switch_input
            status_label = self.input_status_label
            
        if not switch:
            self._show_error(f"{switch_type.capitalize()} switch device not connected")
            return
            
        try:
            # Set the channel
            switch.set_channel(channel)
            
            # Verify it was set
            time.sleep(0.1)  # Small delay
            current = switch.get_channel()
            
            if current == channel:
                status_label.configure(
                    text=f"Current Channel: {current} ✓",
                    text_color="green"
                )
            else:
                status_label.configure(
                    text=f"Current Channel: {current} (Failed to set {channel})",
                    text_color="red"
                )
                
        except Exception as e:
            self._show_error(f"Failed to set channel: {e}")

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
                if not self.switch_output:
                    raise ValueError("Output switch device not available but 'Measure using switch' is selected")
                
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
            # Use the shared module to create headers
            headers.extend(SwitchMeasurements.create_headers_with_switch(
                self.switch_channels, self.selected_unit
            ))
        else:
            # Headers for direct Thorlabs measurements
            if self.thorlabs:
                devices = self.thorlabs if isinstance(self.thorlabs, list) else [self.thorlabs]
                headers.extend(SwitchMeasurements.create_headers_thorlabs(
                    len(devices), self.selected_unit
                ))
        
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
        # Get the first Thorlabs device (connected to switch output)
        thorlabs_device = self.thorlabs[0] if isinstance(self.thorlabs, list) else self.thorlabs
        
        return SwitchMeasurements.measure_with_switch(
            self.switch_output, thorlabs_device, self.switch_channels, self.selected_unit
    )

    def _measure_thorlabs_direct(self):
        """Measure power directly from Thorlabs devices (no switch)"""
        return SwitchMeasurements.measure_thorlabs_direct(self.thorlabs, self.selected_unit)

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

    # def run_path_sequence(self, path_list, delay=0.5):
    #     """
    #     Run each path (JSON dict) in path_list with a delay between each.
    #     Applies phase logic for each step.
    #     Measures from 2 Thorlabs devices after each step and saves results to CSV at the end.
    #     """

    #     create_label_mapping, apply_grid_mapping = get_mapping_functions(self.grid_size)
    #     label_map = create_label_mapping(int(self.grid_size.split('x')[0]))

    #     results = []
    #     headers = ["timestamp", "step", "thorlabs1_uW", "thorlabs2_uW"]

    #     def run_next(index):
    #         if index >= len(path_list):
    #             # Export results
    #             if results:
    #                 self._export_results_to_csv(results, headers)
    #                 print("\nPath sequence complete!")
    #                 # Reset phases to zero
    #                 zero_config = self._create_zero_config()
    #                 apply_grid_mapping(self.qontrol, zero_config, self.grid_size)
    #                 print("All values reset to zero")
    #             else:
    #                 print("\nNo measurements collected.")
    #             return

    #         # Update the global grid config
    #         AppData.default_json_grid = path_list[index]
    #         print(f"Applying path {index+1}/{len(path_list)}: {AppData.default_json_grid}")
    #         # Optionally update the grid UI
    #         self.custom_grid.import_paths_json(json.dumps(AppData.default_json_grid))
    #         # Run your phase application logic
    #         self.apply_phase_new()

    #         # Thorlabs measurements (use only the first two devices)
    #         thorlabs_values = [0.0, 0.0]
    #         if self.thorlabs:
    #             devices = self.thorlabs if isinstance(self.thorlabs, list) else [self.thorlabs]
    #             for i in range(2):
    #                 try:
    #                     thorlabs_values[i] = devices[i].read_power(unit=self.selected_unit)
    #                 except Exception as e:
    #                     print(f"Error reading Thorlabs {i}: {e}")
    #                     thorlabs_values[i] = 0.0

    #         # Record results with timestamp
    #         current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #         row = [current_timestamp, index+1, thorlabs_values[0], thorlabs_values[1]]
    #         results.append(row)

    #         # Print current values
    #         print(f"Step {index+1} measurements:")
    #         print(f"  Thorlabs 1: {thorlabs_values[0]:.3f} {self.selected_unit}")
    #         print(f"  Thorlabs 2: {thorlabs_values[1]:.3f} {self.selected_unit}")

    #         # Schedule the next path after the delay
    #         self.after(int(delay * 1000), lambda: run_next(index + 1))

    #     try:
    #         run_next(0)
    #     except Exception as e:
    #         print(f"Experiment failed: {e}")
    #         import traceback
    #         traceback.print_exc()


    # def _start_status_updates(self):
    #     """Start periodic status updates"""
    #     self._update_system_status()
    #     self.after(10000, self._start_status_updates)

    # def _update_system_status(self):
    #     """Update both status and error displays"""
    #     try:
    #         self._capture_output(self.qontrol.show_errors, self.error_display)
    #         self._capture_output(self.qontrol.show_status, self.status_display)
    #     except Exception as e:
    #         self._show_error(f"Status update failed: {str(e)}")


    def run_path_sequence(self, path_list, delay=0.5):
        """
        Run each path (JSON dict) in path_list with a delay between each.
        Applies phase logic for each step.
        Measures from 2 Thorlabs devices after each step and saves results to CSV at the end.
        """
        create_label_mapping, apply_grid_mapping = get_mapping_functions(self.grid_size)
        label_map = create_label_mapping(int(self.grid_size.split('x')[0]))

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

            # --- Use label_map to apply phase for each cross_label ---
            grid_config = path_list[index]
            phase_grid_config = copy.deepcopy(grid_config)
            for cross_label, data in grid_config.items():
                if cross_label not in label_map:
                    continue
                theta_ch, phi_ch = label_map[cross_label]
                theta_val = data.get("theta", "0")
                phi_val = data.get("phi", "0")

                # Process theta channel
                if theta_ch is not None and theta_val:
                    key = f"{cross_label}_theta"
                    calibration = AppData.phase_calibration_data.get(key)
                    if calibration:
                        try:
                            theta_float = float(theta_val)
                            current_theta = self._calculate_current_for_phase_json(key, theta_float)
                            if current_theta is not None:
                                current_theta = round(current_theta, 5)
                                phase_grid_config[cross_label]["theta"] = str(current_theta)
                        except Exception as e:
                            print(f"{cross_label}:θ ({str(e)})")

                # Process phi channel
                if phi_ch is not None and phi_val:
                    key = f"{cross_label}_phi"
                    calibration = AppData.phase_calibration_data.get(key)
                    if calibration:
                        try:
                            phi_float = float(phi_val)
                            current_phi = self._calculate_current_for_phase_json(key, phi_float)
                            if current_phi is not None:
                                current_phi = round(current_phi, 5)
                                phase_grid_config[cross_label]["phi"] = str(current_phi)
                        except Exception as e:
                            print(f"{cross_label}:φ ({str(e)})")

            # Apply the calculated phase grid config to the device
            try:
                config_json = json.dumps(phase_grid_config)
                apply_grid_mapping(self.qontrol, config_json, self.grid_size)
            except Exception as e:
                print(f"Device update failed: {str(e)}")

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
        """Start periodic status updates (non-blocking)"""
        self._update_system_status()
        self.after(10000, self._start_status_updates)

    def _update_system_status(self):
        """Update both status and error displays in a background thread"""
        def worker():
            try:
                # Capture outputs as strings (not updating UI here)
                error_output = self._capture_output_str(self.qontrol.show_errors)
                status_output = self._capture_output_str(self.qontrol.show_status)
                # Schedule UI update in main thread
                self.after(0, lambda: self._update_status_displays(error_output, status_output))
            except Exception as e:
                self.after(0, lambda: self._show_error(f"Status update failed: {str(e)}"))

        threading.Thread(target=worker, daemon=True).start()

    def _capture_output_str(self, device_func):
        """Capture output from device functions as a string (no UI update)"""
        with io.StringIO() as buffer:
            with redirect_stdout(buffer):
                try:
                    device_func()
                except Exception as e:
                    print(f"Error: {str(e)}")
            return buffer.getvalue()

    def _update_status_displays(self, error_output, status_output):
        """Update the error and status displays in the main thread"""
        self.error_display.configure(state="normal")
        self.error_display.delete("1.0", "end")
        self.error_display.insert("1.0", error_output)
        self.error_display.configure(state="disabled")

        self.status_display.configure(state="normal")
        self.status_display.delete("1.0", "end")
        self.status_display.insert("1.0", status_output)
        self.status_display.configure(state="disabled")

            
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

    # def _event_update_handler(self, event=None):
    #     """Handle event-driven updates"""
    #     current = AppData.get_last_selection()
    #     print(f"Current selection: {current['cross']}-{current['arm']}")
    #     # print(self.custom_grid.export_paths_json())
    #     # print(f"Live selection: {current['cross']}-{current['arm']}")
    #     # modes = self.get_cross_modes()  # self refers to Example instance
    #     # for cross_label, mode in modes.items():
    #     #     print(f"{cross_label}: {mode}")


    def _event_update_handler(self, event=None):
        """Handle event-driven updates"""
        current = AppData.get_last_selection()
        selected_labels = current.get('labels', set())
        self._update_selection_display()  # Add this line

        
        # Print the current selection
        print(f"Current selection: {current['cross']}-{current['arm']}")
        
        # Clear graph if no labels are selected
        if not selected_labels:
            self.graph_image_label1.configure(text="No plot to display")
            self.graph_image_label2.configure(text="No plot to display")
            print("Cleared graph - no labels selected")
        else:
            print(f"Selected labels: {selected_labels}")
            # Existing code for handling selections would go here
            # modes = self.get_cross_modes()
            # for cross_label, mode in modes.items():
            #     print(f"{cross_label}: {mode}")

    def _create_status_displays(self):
        """Status displays are now integrated in control panel"""
        pass

    # Add this method to the class
    def _update_selection_display(self):
        """Update the selection display and handle graph clearing"""
        selected_labels = AppData.get_last_selection().get('labels', set())
        
        # Clear graph if no labels are selected
        if not selected_labels:
            self.graph_image_label1.configure(text="No plot to display")
            self.graph_image_label2.configure(text="No plot to display")
            print("Cleared graph - no labels selected")
        else:
            print(f"Selected labels: {selected_labels}")

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
            scale=1.0
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
            # Get current grid configuration
            config = self.custom_grid.export_paths_json()
            if not config:
                raise ValueError("No grid configuration found")

            # Get mapping functions for current grid size
            create_label_mapping, apply_grid_mapping = get_mapping_functions(self.grid_size)
            if not create_label_mapping or not apply_grid_mapping:
                raise ValueError("Failed to get mapping functions")

            # Create label mapping based on grid size
            n = int(self.grid_size.split('x')[0])
            label_map = create_label_mapping(n)
            if not label_map:
                raise ValueError("Failed to create label mapping")

            # Store the phase grid config for later use
            if hasattr(self, 'phase_grid_config'):
                config_to_apply = json.dumps(self.phase_grid_config)
            else:
                config_to_apply = config

            # Apply the configuration to the device
            apply_grid_mapping(self.qontrol, config_to_apply, self.grid_size)
            
            # Update status display
            self._capture_output(self.qontrol.show_status, self.status_display)

        except Exception as e:
            error_msg = f"Device update failed: {str(e)}"
            print(error_msg)  # Log to console
            self._show_error(error_msg)  # Show in UI


    # def _update_device(self):
    #     """Update Qontrol device with current values"""
    #     try:
    #         config = self.custom_grid.export_paths_json()
    #         # apply_grid_mapping(self.qontrol, config, self.grid_size)
    #         # create_label_mapping, apply_grid_mapping = get_mapping_functions(self.grid_size)
    #         create_label_mapping, apply_grid_mapping = get_mapping_functions(self.grid_size)
    #         label_map = create_label_mapping(int(self.grid_size.split('x')[0]))

    #         apply_grid_mapping(self.qontrol, config, self.grid_size)
    #     except Exception as e:
    #         self._show_error(f"Device update failed: {str(e)}")

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

    def _handle_selection_update(self, event=None):
        """Event-driven update handler"""
        if not AppData.selected_labels:
            # Remove images and set text for both labels
            self.graph_image_label1.configure(image=None, text="No plot to display")
            self.graph_image_label2.configure(image=None, text="No plot to display")
            # Remove any references to images to avoid them being displayed
            self.graph_image_label1.image = None
            self.graph_image_label2.image = None
            self._current_image_ref1 = None
            self._current_image_ref2 = None
            # Force UI update
            self.graph_image_label1.update_idletasks()
            self.graph_image_label2.update_idletasks()
            return


    # def _handle_selection_update(self, event=None):
    #     """Event-driven update handler"""
    #     if not AppData.selected_labels:
    #         # Clear graph images and text
    #         self.graph_image_label1.configure(image=None, text="No plot to display")
    #         self.graph_image_label1._image = None  # Remove reference if you use a custom attribute
    #         self._current_image_ref1 = None

    #         if hasattr(self, 'graph_image_label2'):
    #             self.graph_image_label2.configure(image=None, text="No plot to display")
    #             self.graph_image_label2._image = None
    #             self._current_image_ref2 = None

    #         self.graph_image_label1.update_idletasks()
    #         if hasattr(self, 'graph_image_label2'):
    #             self.graph_image_label2.update_idletasks()
    #         return
    # ...existing code for handling selection...

            # self.graph_image_label1.configure(image=None, text="No Resistance plot to display")
            # self.graph_image_label2.configure(image=None, text="No Phase plot to display")


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
            # apply_grid_mapping(self.qontrol, zero_config, self.grid_size)
            create_label_mapping, apply_grid_mapping = get_mapping_functions(self.grid_size)
            apply_grid_mapping(self.qontrol, zero_config, self.grid_size)


            print("Grid cleared and all values set to zero")
            self._capture_output(self.qontrol.show_status, self.status_display)
            self._update_selection_display()  # Add this line


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
            # label_map = create_label_mapping(8)  # Assuming 8x8 
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
        

        print(f"amplitude: {A}, omega: {b}, phase offset: {c}, offset: {d} for channel {channel}")
        print(f"xdatalist_IObar: {self.app.xdatalist_IObar}")
        print(f"xdatalist_IOcross: {self.app.xdatalist_IOcross}")
        print(f"lincubchar_voltage: {self.app.lincubchar_voltage}"  )
        print(f"lincubchar_current: {self.app.lincubchar_current}")
        # print(f"resistancelist: {self.resistancelist}")

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
                
                print(f"r_params[1]: {r_params[1]}")
                print(f"r_params[0]: {r_params[0]}")

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

    # def _get_current_channels(self, event=None):
    #     """Get theta/phi channels for current selection"""
    #     # current = AppData.get_last_selection()
    #     # current = self.custom_grid.last_selection
    #     current = Appdata.selected_labels()
        
        
    #     if not current or 'cross' not in current:
    #         return None, None
        
    #     label_map = create_label_mapping(8)
    #     theta_ch, phi_ch = label_map.get(current['cross'], (None, None))
    #     # print(f"θ{theta_ch}, φ{phi_ch}")
    #     print(f"Current selection: {current['cross']}-{current['arm']}")

    #     return theta_ch, phi_ch

    def _get_current_channels(self, event=None):
        """Get theta/phi channels for current selection using AppData.selected_labels"""
        selected = list(AppData.selected_labels)
        if not selected:
            return None, None

        cross = selected[0]  # Use the first selected label
        # label_map = create_label_mapping(8)

        create_label_mapping, apply_grid_mapping = get_mapping_functions(self.grid_size)
        label_map = create_label_mapping(int(self.grid_size.split('x')[0]))
        theta_ch, phi_ch = label_map.get(cross, (None, None))
        print(f"Current selection: {cross}")

        return theta_ch, phi_ch

    def run_rp_calibration(self):
        """ Run both resistance and phase calibration functions """
        """Run both resistance and phase calibration functions"""
        try:
            self.characterize_resistance()
            self.characterize_phase()
        except Exception as e:
            self._show_error(f"Calibration failed: {str(e)}")
            import traceback
            traceback.print_exc()

    def characterize_resistance(self):
        """Handle resistance characterization button click"""
        try:
            # Get the currently selected channels
            theta_ch, phi_ch = self._get_current_channels()
            if not self.phase_selector:
                raise ValueError("Phase selector not initialized")
                
            # Determine which channel to characterize based on selector widget
            channel_type = self.phase_selector.radio_var.get()
            target_channel = theta_ch if channel_type == "theta" else phi_ch
            
            if target_channel is None:
                raise ValueError("No valid channel selected")
                
            # Execute resistance characterization
            result = self.calibration_utils.characterize_resistance(
                self.qontrol, 
                target_channel
            )
            
            # Store results
            self.resistance_params[target_channel] = result

            # --- Add this block ---
            # label_map = create_label_mapping(8)  # Use your grid size if not 8

            create_label_mapping, apply_grid_mapping = get_mapping_functions(self.grid_size)
            label_map = create_label_mapping(int(self.grid_size.split('x')[0]))


            channel_to_label = {}
            for label, (theta_ch, phi_ch) in label_map.items():
                channel_to_label[theta_ch] = f"{label}_theta"
                channel_to_label[phi_ch] = f"{label}_phi"
            label = channel_to_label.get(target_channel, str(target_channel))
            from app.utils.appdata import AppData
            AppData.update_resistance_calibration(label, {
                "pin": target_channel,
                "resistance_params": {
                    "a_res": float(result['a_res']),
                    "c_res": float(result['c_res']),
                    "d_res": float(result['d_res']),
                    "rmin": float(result['rmin']),
                    "rmax": float(result['rmax']),
                    "alpha_res": float(result['alpha_res'])
                },
                "measurement_data": {
                    "currents": result['currents'],
                    "voltages": result['voltages'],
                    "max_current": float(result['max_current'])
                }
            })
            
            # Update display
            self.mapping_display.configure(state="normal")
            self.mapping_display.delete("1.0", "end")
            self.mapping_display.insert("1.0", f"Resistance Characterization Results:\n\n")
            self.mapping_display.insert("end", f"Channel: {target_channel}\n")
            self.mapping_display.insert("end", f"Min Resistance: {result['rmin']:.2f} Ω\n")
            self.mapping_display.insert("end", f"Max Resistance: {result['rmax']:.2f} Ω\n")
            self.mapping_display.insert("end", f"Alpha: {result['alpha_res']:.4f}\n")
            self.mapping_display.configure(state="disabled")
            
            # Generate and display plot
            current = AppData.get_last_selection()
            fig = self.plot_utils.plot_resistance(
                result['currents'],
                result['voltages'],
                [result['a_res'], result['c_res'], result['d_res']],  # Resistance params
                target_channel,
                current=current,
                channel_type=channel_type,
                phase_selector=self.phase_selector
            )
            
            if fig:
                # Convert plot to image
                buf = io.BytesIO()
                fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                buf.seek(0)
                img = Image.open(buf).copy()

                # Create CTkImage and display in graph tab
                ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(480, 320))
                self.graph_image_label1.configure(image=ctk_image, text="")
                self._current_image_ref1 = ctk_image  # Keep reference
                
                plt.close(fig)  # Clean up matplotlib figure
                    
        except Exception as e:
            self._show_error(f"Resistance characterization failed: {str(e)}")
            import traceback
            traceback.print_exc()

    def characterize_phase(self):
        """Handle phase characterization button click"""
        try:
            # Get the currently selected channels
            theta_ch, phi_ch = self._get_current_channels()
            if not self.phase_selector:
                raise ValueError("Phase selector not initialized")
                
            # Determine which channel to characterize based on selector
            channel_type = self.phase_selector.radio_var.get()
            target_channel = theta_ch if channel_type == "theta" else phi_ch
            
            if target_channel is None:
                raise ValueError("No valid channel selected")
            
            # Get current selection state and IO config from AppData
            current = AppData.get_last_selection()
            cross = current.get('cross', '')
            io_config = AppData.get_io_config(cross)  # This will return 'cross' or 'bar'
            
            # --- Get resistance parameters from AppData ---
            # label_map = create_label_mapping(8)  # Use your grid size if not 8

            create_label_mapping, apply_grid_mapping = get_mapping_functions(self.grid_size)
            label_map = create_label_mapping(int(self.grid_size.split('x')[0]))


            channel_to_label = {}
            for label, (theta_ch_map, phi_ch_map) in label_map.items():
                channel_to_label[theta_ch_map] = f"{label}_theta"
                channel_to_label[phi_ch_map] = f"{label}_phi"
            label = channel_to_label.get(target_channel, str(target_channel))
            resistance_data = AppData.get_resistance_calibration(label)
            if not resistance_data or "resistance_params" not in resistance_data:
                self._show_error(
                    f"No valid resistance calibration data found for {label}.\n"
                    "Please run resistance calibration first."
                )
                return

            print(f"Running phase calibration for channel {target_channel} ({io_config})")

            # Execute phase characterization
            result = self.calibration_utils.characterize_phase(
                self.qontrol,
                self.thorlabs,
                target_channel,
                io_config,
                resistance_data  # pass full dict now
            )
            
            # Store results
            self.phase_params[target_channel] = result

            AppData.update_phase_calibration(label, {
                "pin": target_channel,
                "phase_params": {
                    "io_config": result['io_config'],
                    "amplitude": float(result['amp']),
                    "omega": float(result['omega']),
                    "phase": float(result['phase']),
                    "offset": float(result['offset'])
                },
                "measurement_data": {
                    "currents": result['currents'],
                    "optical_powers": result['optical_powers']
                }
            })
            # Update display
            self.mapping_display.configure(state="normal")
            self.mapping_display.delete("1.0", "end")
            self.mapping_display.insert("1.0", f"Phase Characterization Results:\n\n")
            self.mapping_display.insert("end", f"Channel: {target_channel}\n")
            self.mapping_display.insert("end", f"IO Config: {io_config}\n")
            self.mapping_display.insert("end", f"Amplitude: {result['amp']:.4f}\n")
            self.mapping_display.insert("end", f"omega: {result['omega']}\n")
            self.mapping_display.insert("end", f"Phase: {result['phase']:.4f} rad\n")
            self.mapping_display.configure(state="disabled")
            
            # Generate and display plot
            fig = self.plot_utils.plot_phase(
                result['heating_powers'],
                result['optical_powers'],
                result['fitfunc'],
                result['rawres'][1],
                target_channel,
                io_config,
                current=current,
                channel_type=channel_type
            )
            
            if fig:
                # Convert plot to image
                buf = io.BytesIO()
                fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                buf.seek(0)
                img = Image.open(buf)

                # Create CTkImage and display in graph tab
                ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(480, 320))
                self.graph_image_label2.configure(image=ctk_image, text="")
                self._current_image_ref2 = ctk_image  # Keep reference
                
                buf.close()
                plt.close(fig)  # Clean up matplotlib figure

        except Exception as e:
            self._show_error(f"Phase characterization failed: {str(e)}")
            import traceback
            traceback.print_exc()

    def export_calibration_data(self):
        """Export calibration data to JSON file"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Export Calibration Data",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if file_path:
                saved_path = self.calibration_utils.export_calibration(
                    self.resistance_params,
                    self.phase_params,
                    file_path
                )
                print(f"Calibration data exported to {saved_path}")
        except Exception as e:
            self._show_error(f"Failed to export calibration data: {str(e)}")

    def import_calibration_data(self):
        """Import calibration data from JSON file"""
        try:
            file_path = filedialog.askopenfilename(
                title="Import Calibration Data",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if file_path:
                resistance_params, phase_params = self.calibration_utils.import_calibration(file_path)
                self.resistance_params = resistance_params
                self.phase_params = phase_params
                print(f"Calibration data imported from {file_path}")
                # Clear selection after import
                AppData.update_last_selection("", "")
                self.replot_current_selection()  # Show "No plot to display"
        except Exception as e:
            self._show_error(f"Failed to import calibration data: {str(e)}")

    def replot_current_selection(self):
        """Replot the graph for the currently selected node using imported calibration data."""
        current = AppData.get_last_selection()
        if not current or not current.get('cross'):
            # No selection: clear plots and show message
            self.graph_image_label1.configure(image=None, text="No plot to display")
            self.graph_image_label2.configure(image=None, text="No plot to display")
            self._current_image_ref1 = None
            self._current_image_ref2 = None
            return

        # label_map = create_label_mapping(8)  # Or use self.grid_size if dynamic

        create_label_mapping, apply_grid_mapping = get_mapping_functions(self.grid_size)
        label_map = create_label_mapping(int(self.grid_size.split('x')[0]))
        
        theta_ch, phi_ch = label_map.get(current['cross'], (None, None))
        if not self.phase_selector:
            return  # Phase selector not initialized

        channel_type = self.phase_selector.radio_var.get()
        target_channel = theta_ch if channel_type == "theta" else phi_ch
        channel_to_label = {}
        for lbl, (th, ph) in label_map.items():
            channel_to_label[th] = f"{lbl}_theta"
            channel_to_label[ph] = f"{lbl}_phi"
        label = channel_to_label.get(target_channel, str(target_channel))

        # Resistance plot
        if label in self.resistance_params:
            params = self.resistance_params[label]
            fig = self.plot_utils.plot_resistance(
                params['currents'],
                params['voltages'],
                [params['a'], params['c'], params['d']],
                params.get('pin', target_channel),
                current=current,
                channel_type=channel_type,
                phase_selector=self.phase_selector
            )
            if fig:
                buf = io.BytesIO()
                fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                buf.seek(0)
                img = Image.open(buf)
                ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(480, 320))
                self.graph_image_label1.configure(image=ctk_image, text="")
                self._current_image_ref1 = ctk_image
                plt.close(fig)
        # Try phase plot
        if label in self.phase_params:
            params = self.phase_params[label]
            fig = self.plot_utils.plot_phase(
                params['currents'],
                params['optical_powers'],
                params.get('fitfunc', lambda x, *a: x),  # fallback if missing
                [params['amp'], params['omega'], params['phase'], params['offset']],
                params.get('pin', target_channel),
                params['io_config'],
                current=current,
                channel_type=channel_type
            )
            if fig:
                buf = io.BytesIO()
                fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                buf.seek(0)
                img = Image.open(buf)
                ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(480, 320))
                self.graph_image_label2.configure(image=ctk_image, text="")
                self._current_image_ref2 = ctk_image
                plt.close(fig)

    def update_resistance_plot(self):
        """Generate and display resistance plot for the currently selected label."""
        if not AppData.selected_labels:
            self.graph_image_label1.configure(image=None, text="No plot to display")
            self._current_image_ref1 = None
            return

        selected = list(AppData.selected_labels)
        cross_label = selected[-1] if selected else ""
        # Get channel type from your selector widget
        channel_type = self.phase_selector.radio_var.get() if self.phase_selector else "theta"
        key = f"{cross_label}_{channel_type}"
        result = AppData.resistance_calibration_data.get(key)

        if not result:
            self.graph_image_label1.configure(image=None, text="No plot to display")
            self._current_image_ref1 = None
            return

        fig = self.plot_utils.plot_resistance(
            result['currents'],
            result['voltages'],
            [result['a'], result['c'], result['d']],
            result['pin'],  # or result['target_channel'] if that's your key
            channel_type=channel_type
        )

        if fig:
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            img = Image.open(buf)

            ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(480, 320))
            self.graph_image_label1.configure(image=ctk_image, text="")
            self._current_image_ref1 = ctk_image

            plt.close(fig)
        else:
            self.graph_image_label1.configure(image=None, text="No plot to display")
            self._current_image_ref1 = None

    def update_phase_plot(self):
        """Generate and display phase plot for the currently selected label."""
        if not AppData.selected_labels:
            self.graph_image_label2.configure(image=None, text="No plot to display")
            self._current_image_ref2 = None
            return

        selected = list(AppData.selected_labels)
        cross_label = selected[-1] if selected else ""
        # Retrieve your result data for the selected label
        # Example: result = AppData.phase_calibration_data.get(f"{cross_label}_theta") or similar
        # You need to adjust this line to match your data structure:
        result = ...  # <-- get the result dict for the selected label

        if not result:
            self.graph_image_label2.configure(image=None, text="No plot to display")
            self._current_image_ref2 = None
            return

        # Generate the plot
        fig = self.plot_utils.plot_phase(
            result['currents'],
            result['optical_powers'],
            result['fitfunc'],
            result['rawres'][1],
            result['target_channel'],
            result['io_config'],
            channel_type=result.get('channel_type', None)
        )

        if fig:
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            img = Image.open(buf)

            ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(480, 320))
            self.graph_image_label2.configure(image=ctk_image, text="")
            self._current_image_ref2 = ctk_image  # Keep reference

            plt.close(fig)
        else:
            self.graph_image_label2.configure(image=None, text="No plot to display")
            self._current_image_ref2 = None

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


    def export_appdata_calibration(self):
        """
        Export AppData's resistance and phase calibration data to a JSON file.
        """

        file_path = filedialog.asksaveasfilename(
            title="Export AppData Calibration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return  # User cancelled

        data = {
            "resistance_calibration_data": AppData.resistance_calibration_data,
            "phase_calibration_data": AppData.phase_calibration_data
        }
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            print(f"AppData calibration exported to {file_path}")
        except Exception as e:
            print(f"Failed to export AppData calibration: {e}")


    def apply_phase_new_json(self):
        """
        Apply phase settings to the entire grid based on phase calibration data from AppData.
        Processes all theta and phi values in the current grid configuration.
        """
        try:
            # Get current grid configuration
            grid_config = json.loads(self.custom_grid.export_paths_json())
            if not grid_config:
                self._show_error("No grid configuration found")
                return

            # Get label mapping for current grid size
            create_label_mapping, apply_grid_mapping = get_mapping_functions(self.grid_size)
            label_map = create_label_mapping(int(self.grid_size.split('x')[0]))

            # Create new configuration and tracking lists
            phase_grid_config = copy.deepcopy(grid_config)
            applied_channels = []
            failed_channels = []

            # Process each cross in the grid
            for cross_label, data in grid_config.items():
                # Skip if not in mapping
                if cross_label not in label_map:
                    continue

                # Process theta value
                theta_val = self.interpolated_theta.get(cross_label) if self.interpolation_enabled else data.get("theta", "0")
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
                        channel = f"{cross_label}_phi"
                        current_phi = self._calculate_current_for_phase_new_json(channel, phi_float)
                        
                        if current_phi is not None:
                            current_phi = round(current_phi, 5)
                            phase_grid_config[cross_label]["phi"] = str(current_phi)
                            applied_channels.append(f"{cross_label}:φ = {current_phi:.5f} mA")
                        else:
                            failed_channels.append(f"{cross_label}:φ (no calibration)")
                    except Exception as e:
                        failed_channels.append(f"{cross_label}:φ ({str(e)})")

            # Store config and update displays
            self.phase_grid_config = phase_grid_config
            self._update_phase_results_display(applied_channels, failed_channels)

            # Apply configuration to device
            try:
                config_json = json.dumps(phase_grid_config)
                apply_grid_mapping(self.qontrol, config_json, self.grid_size)
                self._capture_output(self.qontrol.show_status, self.status_display)
            except Exception as e:
                self._show_error(f"Device update failed: {str(e)}")

        except Exception as e:
            self._show_error(f"Failed to apply phases: {str(e)}")
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
            print(f"[DEBUG] Entering _calculate_current_for_phase_new_json with calib_key={calib_key}, phase_value={phase_value}")
            res_cal = AppData.resistance_calibration_data.get(calib_key)
            phase_cal = AppData.phase_calibration_data.get(calib_key)
            # Get resistance calibration data
            res_cal = AppData.resistance_calibration_data.get(calib_key)
            print(f"[DEBUG] res_cal: {res_cal}")
            if not res_cal:
                print(f"[ERROR] No resistance calibration for {calib_key}")
                return None

            res_params = res_cal.get("resistance_params", {})
            print(f"[DEBUG] res_params: {res_params}")
            if not res_params:
                print(f"[ERROR] No resistance_params for {calib_key}")
                return None

            # Get phase calibration data
            phase_cal = AppData.phase_calibration_data.get(calib_key)
            print(f"[DEBUG] phase_cal: {phase_cal}")
            if not phase_cal:
                print(f"[ERROR] No phase calibration for {calib_key}")
                return None

            phase_params = phase_cal.get("phase_params", {})
            print(f"[DEBUG] phase_params: {phase_params}")
            if not phase_params:
                print(f"[ERROR] No phase_params for {calib_key}")
                return None

            # --- FIX: Do not double index ---
            try:
                c_res = res_params['c_res']     # kΩ
                a_res = res_params['a_res']     # V/(mA)³
                A = phase_params['amplitude']   # mW
                b = phase_params['omega']       # rad/mW
                c = phase_params['phase']       # rad
                d = phase_params['offset']      # mW
            except Exception as e:
                print(f"[ERROR] Failed to extract parameters: {e}")
                print(f"[DEBUG] res_params: {res_params}")
                print(f"[DEBUG] phase_params: {phase_params}")
                return None

            print(f"[DEBUG] Extracted: c_res={c_res}, a_res={a_res}, A={A}, b={b}, c={c}, d={d}")

            if phase_value < c/np.pi:
                print(f"Warning: Phase {phase_value}π is less than offset phase {c/np.pi}π for {calib_key}")
                phase_value = phase_value + 2
                print(f"Using adjusted phase value: {phase_value}π")

            # Calculate heating power for this phase shift
            P_mW = abs((phase_value*np.pi - c) / b)    # Power in mW
            print(f"[DEBUG] Calculated heating power P={P_mW} mW")

            # Define symbols for solving equation
            I = sp.symbols('I', real=True, positive=True)

            # R0 is the linear resistance (same as c_res)
            R0 = c_res  # kΩ
            alpha = a_res/R0 if R0 != 0 else 0  
            print(f"[DEBUG] P_mW={P_mW} mW, R0={R0} kΩ, alpha={alpha} (1/mA²)")

            # Define equation: P/R0 = I²(1 + alpha*I²)
            eq = sp.Eq(P_mW/R0, I**2 * (1 + alpha * I**2))
            print(f"[DEBUG] Equation: {P_mW}/{R0} = I² × (1 + {alpha}×I²)")

            # Solve the equation
            solutions = sp.solve(eq, I)
            print(f"[DEBUG] Solutions: {solutions}")

            # Filter and choose the real, positive solution
            positive_solutions = [sol.evalf() for sol in solutions if sol.is_real and sol.evalf() > 0]
            print(f"[DEBUG] Positive solutions: {positive_solutions}")
            if positive_solutions:
                print(f"-> Calculated Current for {calib_key}: {positive_solutions[0]:.4f} mA")
                I_mA = positive_solutions[0] 
                return I_mA
            else:
                print(f"[ERROR] No positive solution for {calib_key}, fallback to linear model")
                return None

        except Exception as e:
            print(f"[EXCEPTION] Error calculating current for {calib_key}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    # def _calculate_current_for_phase_new_json(self, calib_key, phase_value):
    #     """
    #     Calculate current for a phase value using the new calibration format.
        
    #     Args:
    #         calib_key: str, calibration key (e.g. "A1_theta")
    #         phase_value: float, phase value in π units
            
    #     Returns:
    #         float: Current in mA or None if calculation fails
    #     """
    #     try:


    #         # Get resistance calibration data
    #         res_cal = AppData.resistance_calibration_data.get(calib_key)
    #         if not res_cal:
    #             return None
                
    #         res_params = res_cal.get("resistance_params", {})
    #         if not res_params:
    #             return None

    #         # Get phase calibration data
    #         phase_cal = AppData.phase_calibration_data.get(calib_key)
    #         if not phase_cal:
    #             return None
                
    #         phase_params = phase_cal.get("phase_params", {})
    #         if not phase_params:
    #             return None

    #         c_res = res_cal[calib_key]['resistance_params']['c_res'] * 1000
    #         a_res = res_cal[calib_key]['resistance_params']['a_res'] * 10e9   
    #         A = phase_cal[calib_key]['phase_params']['amplitude'] 
    #         b = phase_cal[calib_key]['phase_params']['omega']
    #         c = phase_cal[calib_key]['phase_params']['phase']
    #         d = phase_cal[calib_key]['phase_params']['offset']

    #         # c_res = 1036.6441840655363
    #         # a_res = 3621062.146585479 
    #         # A = 0.6005338378507308
    #         # b = 0.2583951254144626
    #         # c = 0.4247100614593249 #3.1415926535897927
    #         # d = 0.6021712385768999
            

    #             # amplitude: 0.0908441893692287, omega: 0.2762131249289536, phase offset: 3.1415926535897927, offset: 0.09066978105949058 for channel 21
    #             # r_params[1]: 1008.6807070542391
    #             # r_params[0]: 3419549.948304372
    #         if phase_value < c/np.pi:
    #             print(f"Warning: Phase {phase_value}π is less than offset phase {c/np.pi}π for channel {channel}")
    #             phase_value = phase_value + 2
    #             print(f"Using adjusted phase value: {phase_value}π")

    #         # Calculate heating power for this phase shift
    #         P = abs((phase_value*np.pi - c) / b)
                

    #         # Define symbols for solving equation
    #         I = sp.symbols('I')
    #         P_watts = P/1000  # Convert to watts
    #         R0 = c_res  # Linear resistance term (c)
    #         alpha = a_res/R0 if R0 != 0 else 0  # Nonlinearity parameter (a/c)
            
    #         # Define equation: P/R0 = I^2 + alpha*I^4
    #         eq = sp.Eq(P_watts/R0, I**2 + alpha*I**4)
            
    #         # Solve the equation
    #         solutions = sp.solve(eq, I)

    #         # Filter and choose the real, positive solution
    #         positive_solutions = [sol.evalf() for sol in solutions if sol.is_real and sol.evalf() > 0]
    #         if positive_solutions:
    #             print(f"-> Calculated Current for {calib_key}: {positive_solutions[0]:.4f} A")
    #             I_mA = positive_solutions[0] * 1000  # Convert to mA
    #             return I_mA
    #         else:
    #             # Fallback to linear model
    #             print(f"error")

    #     except Exception as e:
    #         print(f"Error calculating current: {str(e)}")
    #         return None
        


    # def _calculate_current_for_phase_new_json(self, calib_key, phase_value):
    #     """
    #     Calculate current for a phase value using the new calibration format.
        
    #     Args:
    #         calib_key: str, calibration key (e.g. "A1_theta")
    #         phase_value: float, phase value in π units
            
    #     Returns:
    #         float: Current in mA or None if calculation fails
    #     """
    #     try:
    #         # Get resistance calibration data
    #         res_cal = AppData.resistance_calibration_data.get(calib_key)
    #         if not res_cal:
    #             return None
                
    #         res_params = res_cal.get("resistance_params", {})
    #         if not res_params:
    #             return None

    #         # Get phase calibration data
    #         phase_cal = AppData.phase_calibration_data.get(calib_key)
    #         if not phase_cal:
    #             return None
                
    #         phase_params = phase_cal.get("phase_params", {})
    #         if not phase_params:
    #             return None
    #         # Extract resistance parameters
    #         a_res = res_params.get("a")  # Cubic term
    #         c_res = res_params.get("c")  # Linear term
    #         if c_res == 0:
    #             print("-> Error: R0 (c) parameter is zero.")
    #             return None
            
    #         # Extract phase parameters
    #         b_param = phase_params.get("frequency", 1.0) * 2 * np.pi  # Convert Hz to rad/s
    #         c_param = phase_params.get("phase", 0.0)  # Phase offset in radians
    #         io_conf = phase_params.get('io_config', 'cross_state')
    #         if b_param is None or c_param is None:
    #             print("-> Error: Missing phase parameters (frequency, phase offset).")
    #             return None
    #         # Convert frequency to b in rad/mW
    #         b = b_param * 2 * np.pi            

    #         visibility   = phase_params.get('amplitude', 1.0)/phase_params.get('offset', 1.0)

    #         # Heating power for Pi phase shift
    #         P_pi = (abs((np.pi - c_param) / b))/100 #Heating power of phi phase shift

    #         # Check phase range and adjust if needed
    #         if phase_value < c_param/np.pi:
    #             print(f"Warning: Phase {phase_value}π is less than offset phase {c_param/np.pi}π")
    #             phase_value = phase_value + 2
    #             print(f"Using adjusted phase value: {phase_value}π")

    #         # if io_conf == 'cross_state':
    #         #     # invert around π
    #         #     phase_value_lin = np.pi - phase_value
    #         #     print(f"-> Cross state adjustment: target_lin = {phase_value_lin:.4f} rad")
    #         # else:
    #         #     phase_value_lin = phase_value

    #         P_mw = abs((phase_value*np.pi - c_param) / b)
    #         print(f"-> Required Power: {P_mw:.4f} mW (io_config={io_conf})")

    #         # Convert to Watts
    #         P_w = P_mw / 1000.0

    #         # Resistance model: P = I^2*R0 + (a_res/c_res)*I^4*R0
    #         R0 = c_res * 1000.0
    #         alpha = a_res / c_res

    #         # Compute current
    #         if alpha == 0:
    #             I_A = np.sqrt(P_w / R0)
    #         else:
    #             I = sp.symbols('I')
    #             eq = sp.Eq(P_pi/R0, I**2 + alpha*I**4)
    #             # eq = sp.Eq(P_w/R0, I**2 + alpha*I**4)
    #             # eq = sp.Eq(alpha * I**4 + I**2 - (P_w / R0), 0)
    #             sols = sp.solve(eq, I)
    #             real_pos = [s.evalf() for s in sols if s.is_real and s.evalf() > 0]
    #             if not real_pos:
    #                 print("-> Error: No valid current solution.")
    #                 return None
    #             I_A = real_pos[0]

    #         I_mA = float(I_A * 1000)
    #         print(f"-> Calculated Current: {I_mA:.4f} mA")
    #         return I_mA


    #     except Exception as e:
    #         print(f"Error calculating current: {str(e)}")
    #         return None
        


    # def _calculate_current_for_phase_new_json(self, calib_key, phase_value):
    #     """
    #     Calculate current for a phase value using the new calibration format.
        
    #     Args:
    #         calib_key: str, calibration key (e.g. "A1_theta")
    #         phase_value: float, phase value in π units
            
    #     Returns:
    #         float: Current in mA or None if calculation fails
    #     """
    #     try:
    #         # Get resistance calibration data
    #         res_cal = AppData.resistance_calibration_data.get(calib_key)
    #         if not res_cal:
    #             return None
                
    #         res_params = res_cal.get("resistance_params", {})
    #         if not res_params:
    #             return None

    #         # Get phase calibration data
    #         phase_cal = AppData.phase_calibration_data.get(calib_key)
    #         if not phase_cal:
    #             return None
                
    #         phase_params = phase_cal.get("phase_params", {})
    #         if not phase_params:
    #             return None
    #         # Extract resistance parameters
    #         a_res = res_params.get("a")  # Cubic term
    #         c_res = res_params.get("c")  # Linear term
    #         if c_res == 0:
    #             print("-> Error: R0 (c) parameter is zero.")
    #             return None
            
    #         # Extract phase parameters
    #         b_param = phase_params.get("frequency", 1.0) * 2 * np.pi  # Convert Hz to rad/s
    #         c_param = phase_params.get("phase", 0.0)  # Phase offset in radians
    #         io_conf = phase_params.get('io_config', 'cross_state')
    #         if b_param is None or c_param is None:
    #             print("-> Error: Missing phase parameters (frequency, phase offset).")
    #             return None
    #         # Convert frequency to b in rad/mW
    #         b = b_param * 2 * np.pi            
    #         # Check phase range and adjust if needed
    #         if phase_value < c_param/np.pi:
    #             print(f"Warning: Phase {phase_value}π is less than offset phase {c_param/np.pi}π")
    #             phase_value = phase_value + 2
    #             print(f"Using adjusted phase value: {phase_value}π")

    #         # if io_conf == 'cross_state':
    #         #     # invert around π
    #         #     phase_value_lin = np.pi - phase_value
    #         #     print(f"-> Cross state adjustment: target_lin = {phase_value_lin:.4f} rad")
    #         # else:
    #         #     phase_value_lin = phase_value

    #         P_mw = abs((phase_value - c_param) / b)
    #         print(f"-> Required Power: {P_mw:.4f} mW (io_config={io_conf})")

    #         # Convert to Watts
    #         P_w = P_mw / 1000.0

    #         # Resistance model: P = I^2*R0 + (a_res/c_res)*I^4*R0
    #         R0 = c_res * 1000.0
    #         alpha = a_res / c_res

    #         # Compute current
    #         if alpha == 0:
    #             I_A = np.sqrt(P_w / R0)
    #         else:
    #             I = sp.symbols('I')
    #             eq = sp.Eq(alpha * I**4 + I**2 - (P_w / R0), 0)
    #             sols = sp.solve(eq, I)
    #             real_pos = [s.evalf() for s in sols if s.is_real and s.evalf() > 0]
    #             if not real_pos:
    #                 print("-> Error: No valid current solution.")
    #                 return None
    #             I_A = real_pos[0]

    #         I_mA = float(I_A * 1000)
    #         print(f"-> Calculated Current: {I_mA:.4f} mA")
    #         return I_mA


    #     except Exception as e:
    #         print(f"Error calculating current: {str(e)}")
    #         return None


    def _update_phase_results_display(self, applied_channels, failed_channels):
        """Helper to update the mapping display with phase application results"""
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


    # def apply_phase_new_json(self):
    #     """
    #     Apply phase settings to the entire grid based on calibration data in AppData.
    #     Uses the new calibration format: {"A1_theta": {...}, ...}
    #     """
    #     try:
    #         grid_config = json.loads(self.custom_grid.export_paths_json())
    #         if not grid_config:
    #             self._show_error("No grid configuration found")
    #             return

    #         create_label_mapping, apply_grid_mapping = get_mapping_functions(self.grid_size)
    #         label_map = create_label_mapping(int(self.grid_size.split('x')[0]))

    #         phase_grid_config = copy.deepcopy(grid_config)
    #         applied_channels = []
    #         failed_channels = []

    #         for cross_label, data in grid_config.items():
    #             if cross_label not in label_map:
    #                 continue

    #             theta_ch, phi_ch = label_map[cross_label]
    #             theta_val = data.get("theta", "0")
    #             phi_val = data.get("phi", "0")

    #             # Process theta channel
    #             if theta_ch is not None and theta_val:
    #                 key = f"{cross_label}_theta"
    #                 calibration = AppData.phase_calibration_data.get(key)
    #                 if calibration:
    #                     try:
    #                         theta_float = float(theta_val)
    #                         current_theta = self._calculate_current_for_phase_json(key, theta_float)
    #                         if current_theta is not None:
    #                             current_theta = round(current_theta, 5)
    #                             phase_grid_config[cross_label]["theta"] = str(current_theta)
    #                             applied_channels.append(f"{cross_label}:θ = {current_theta:.5f} mA")
    #                         else:
    #                             failed_channels.append(f"{cross_label}:θ (no calibration)")
    #                     except Exception as e:
    #                         failed_channels.append(f"{cross_label}:θ ({str(e)})")
    #                 else:
    #                     failed_channels.append(f"{cross_label}:θ (missing calibration)")

    #             # Process phi channel
    #             if phi_ch is not None and phi_val:
    #                 key = f"{cross_label}_phi"
    #                 calibration = AppData.phase_calibration_data.get(key)
    #                 if calibration:
    #                     try:
    #                         phi_float = float(phi_val)
    #                         current_phi = self._calculate_current_for_phase_json(key, phi_float)
    #                         if current_phi is not None:
    #                             current_phi = round(current_phi, 5)
    #                             phase_grid_config[cross_label]["phi"] = str(current_phi)
    #                             applied_channels.append(f"{cross_label}:φ = {current_phi:.5f} mA")
    #                         else:
    #                             failed_channels.append(f"{cross_label}:φ (no calibration)")
    #                     except Exception as e:
    #                         failed_channels.append(f"{cross_label}:φ ({str(e)})")
    #                 else:
    #                     failed_channels.append(f"{cross_label}:φ (missing calibration)")

    #         self.phase_grid_config = phase_grid_config

    #         # Update mapping display
    #         self.mapping_display.configure(state="normal")
    #         self.mapping_display.delete("1.0", "end")
    #         self.mapping_display.insert("1.0", "Phase Application Results:\n\n")
    #         self.mapping_display.insert("end", "Successfully applied:\n")
    #         for channel in applied_channels:
    #             self.mapping_display.insert("end", f"• {channel}\n")
    #         if failed_channels:
    #             self.mapping_display.insert("end", "\nFailed to apply:\n")
    #             for channel in failed_channels:
    #                 self.mapping_display.insert("end", f"• {channel}\n")
    #         self.mapping_display.configure(state="disabled")

    #         print(phase_grid_config)
    #         self._capture_output(self.qontrol.show_status, self.status_display)

    #         try:
    #             config_json = json.dumps(phase_grid_config)
    #             apply_grid_mapping(self.qontrol, config_json, self.grid_size)
    #         except Exception as e:
    #             self._show_error(f"Device update failed: {str(e)}")

    #     except Exception as e:
    #         self._show_error(f"Failed to apply phases: {str(e)}")
    #         import traceback
    #         traceback.print_exc()
    #         return None


    # def _calculate_current_for_phase_json(self, calibration_key, phase_value):
    #     """
    #     Calculate current for a given phase value using new calibration format.
    #     Args:
    #         calibration_key: e.g. "A1_theta" or "B2_phi"
    #         phase_value: value in pi units
    #     Returns:
    #         current in mA or None
    #     """
    #     calibration = AppData.phase_calibration_data.get(calibration_key)
    #     if not calibration:
    #         return None

    #     phase_params = calibration.get("phase_params", {})
    #     resistance_cal_key = calibration_key  # Use same key for resistance
    #     resistance_cal = AppData.resistance_calibration_data.get(resistance_cal_key)
    #     resistance_params = resistance_cal.get("resistance_params", {}) if resistance_cal else None

    #     return self._calculate_current_from_params_json(phase_value, phase_params, resistance_params)


    # def _calculate_current_from_params_json(self, label, channel, phase_value):
    #     """
    #     Calculate current using calibration data for a given label and phase value.
        
    #     Args:
    #         label: str, like "A1_theta"
    #         channel: int, used for fallback resistance
    #         phase_value: float, phase in π units

    #     Returns:
    #         Current in mA or None
    #     """
    #     try:
    #         # === Phase calibration lookup ===
    #         phase_entry = self.app.phase_calibration_data.get(label, {})
    #         phase_params = phase_entry.get("phase_params", {})

    #         b = phase_params.get("frequency", 1.0) * 2 * np.pi  # omega in rad/s
    #         c = phase_params.get("phase", 0.0)                  # offset phase in radians

    #         # Warn if phase is less than offset, wrap like original function
    #         if phase_value < c / np.pi:
    #             print(f"Warning: Phase {phase_value}π is less than offset phase {c/np.pi}π for label {label}")
    #             phase_value += 2
    #             print(f"Using adjusted phase value: {phase_value}π")

    #         # Convert to radians and compute heating power
    #         phase_radians = phase_value * np.pi
    #         P = abs((phase_radians - c) / b)  # power in mW

    #         # === Resistance calibration lookup ===
    #         resistance_entry = self.app.resistance_calibration_data.get(label, {})
    #         resistance_params = resistance_entry.get("resistance_params", {})

    #         a = resistance_params.get("a")
    #         c_res = resistance_params.get("c")

    #         if a is not None and c_res is not None:
    #             # Solve: P = I^2 * (a*I^2 + c)
    #             I_sym = sp.symbols('I', real=True, positive=True)
    #             P_watts = P / 1000  # mW to W
    #             R0 = c_res
    #             alpha = a / R0 if R0 != 0 else 0

    #             eq = sp.Eq(P_watts / R0, I_sym**2 + alpha * I_sym**4)
    #             solutions = sp.solve(eq, I_sym)
    #             positive = [sol.evalf() for sol in solutions if sol.is_real and sol.evalf() > 0]
    #             if positive:
    #                 return float(round(1000 * positive[0], 2))  # return in mA

    #             # Fallback linear model
    #             I = np.sqrt(P / R0) if R0 else 0
    #             return float(round(I, 5))  # mA
    #         else:
    #             # Fallback: linear resistance from list or default
    #             print(f"No resistance found for {channel}")

    #     except Exception as e:
    #         print(f"Error in _calculate_current_from_params_json: {e}")
    #         return None



    # def _calculate_current_from_params_json(self, channel, phase_value, phase_params, resistance_params):
    #     """
    #     Calculate current from phase and resistance parameters in new calibration format.
    #     Args:
    #         channel: int channel number (used to retrieve fallback resistance if needed)
    #         phase_value: value in π units
    #         phase_params: dict with 'frequency' (Hz) and 'phase' (radians)
    #         resistance_params: dict with 'a' and 'c' from calibration
    #     Returns:
    #         current in mA or None
    #     """
    #     try:
    #         # Extract phase fit parameters
    #         b = phase_params.get("frequency", 1.0) * 2 * np.pi  # omega in rad/s
    #         c = phase_params.get("phase", 0.0)                  # offset phase in radians

    #         # Check if phase is within valid range
    #         if phase_value < c / np.pi:
    #             print(f"Warning: Phase {phase_value}π is less than offset phase {c/np.pi}π for channel {channel}")
    #             phase_value += 2
    #             print(f"Using adjusted phase value: {phase_value}π")

    #         # Convert to radians
    #         phase_radians = phase_value * np.pi

    #         # Calculate heating power (in mW)
    #         P = abs((phase_radians - c) / b)

    #         # Extract resistance parameters
    #         a = resistance_params.get("a", None) if resistance_params else None
    #         c_res = resistance_params.get("c", None) if resistance_params else None

    #         if a is not None and c_res is not None:
    #             # Use symbolic solver: P = I^2 * (a*I^2 + c)  =>  P/c = I^2 + (a/c) * I^4
    #             I_sym = sp.symbols('I', real=True, positive=True)
    #             P_watts = P / 1000  # Convert to watts
    #             R0 = c_res
    #             alpha = a / R0 if R0 != 0 else 0

    #             eq = sp.Eq(P_watts / R0, I_sym**2 + alpha * I_sym**4)
    #             solutions = sp.solve(eq, I_sym)

    #             positive_solutions = [sol.evalf() for sol in solutions if sol.is_real and sol.evalf() > 0]
    #             if positive_solutions:
    #                 return float(round(1000 * positive_solutions[0], 2))  # Convert to mA
    #             else:
    #                 # Fallback to linear model
    #                 I = np.sqrt(P / R0) if R0 else 0
    #                 return float(round(I, 5))  # mA
    #         else:
    #             # Fallback: use linear resistance estimate from app if available
    #             if hasattr(self, "app") and hasattr(self.app, "linear_resistance_list"):
    #                 R = self.app.linear_resistance_list[channel] if channel < len(self.app.linear_resistance_list) else 50.0
    #             else:
    #                 R = 50.0  # default fallback

    #             I = np.sqrt(P / (R * 1000))  # convert R to ohms
    #             return float(round(1000 * I, 2))  # return mA
    #     except Exception as e:
    #         print(f"Error in _calculate_current_from_params_json: {e}")
    #         return None




    # def _calculate_current_from_params_json(self, phase_value, phase_params, resistance_params):
    #     """
    #     Calculate current from phase and resistance parameters in new calibration format.
    #     Args:
    #         phase_value: value in pi units
    #         phase_params: dict from calibration
    #         resistance_params: dict from calibration
    #     Returns:
    #         current in mA or None
    #     """
    #     try:
    #         # Extract phase fit parameters
    #         b = phase_params.get("frequency", 1.0) * 2 * np.pi  # Hz to rad/s
    #         c = phase_params.get("phase", 0.0)                  # offset phase in radians

    #         # Convert phase_value from pi units to radians
    #         phase_radians = phase_value * np.pi

    #         # Calculate heating power for this phase shift
    #         P = abs((phase_radians - c) / b)  # in mW

    #         # Extract resistance parameters
    #         if resistance_params:
    #             a = resistance_params.get("a", 0.0)
    #             c_res = resistance_params.get("c", 1000.0)
    #             # Solve for current: P = I^2 * (a*I^2 + c)
    #             # P = a*I^4 + c*I^2 → quadratic in I^2

    #             discriminant = c_res**2 + 4*a*P
    #             if discriminant < 0 or a == 0:
    #                 I_squared = P / c_res if c_res != 0 else 0
    #             else:
    #                 I_squared = (-c_res + np.sqrt(discriminant)) / (2*a) if a != 0 else P / c_res
    #             I = np.sqrt(I_squared) if I_squared > 0 else 0
    #             return float(round(I, 5))  # mA
    #         else:
    #             # Fallback to linear resistance
    #             R = 1000.0
    #             I = np.sqrt(P / R)
    #             return float(round(I, 5))  # mA
    #     except Exception as e:
    #         print(f"Error in _calculate_current_from_params: {e}")
    #         return None
