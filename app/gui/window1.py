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

class Window1Content(ctk.CTkFrame):
    def __init__(self, master, channel, fit, IOconfig, app, qontrol, thorlabs, daq, phase_selector=None, grid_size="8x8", **kwargs):
        super().__init__(master, **kwargs)
        self.qontrol = qontrol
        self.thorlabs = thorlabs
        self.daq = daq        
        self.grid_size = grid_size
        self.after_id = None
        self.control_panel = None  
        self.resistance_params: Dict[int, Dict[str, Any]] = {}
        self.calibration_params = {'cross': {}, 'bar': {}}
        self.phase_params = {}
        self.phase_selector = phase_selector
        self.app = app  # Store the AppData instance


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


        # Compact notebook for displays
        notebook = ctk.CTkTabview(inner_frame, height=180, width=300)  # Fixed  height, width
        notebook.grid_propagate(False)
        notebook.grid(row=1, column=0, sticky="nsew", pady=(2, 0))
        inner_frame.grid_columnconfigure(0, weight=1)

        # Graph tab
        graph_tab = notebook.add("Graph")
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

        # Mapping tab
        self.mapping_display = ctk.CTkTextbox(notebook.add("Mapping"))
        self.mapping_display.pack(fill="both", expand=True)
        

        # Status tab
        self.status_display = ctk.CTkTextbox(notebook.add("Status"), state="disabled")
        self.status_display.pack(fill="both", expand=True)
        
        # Measure tab
        measure_tab = notebook.add("Measure")
        measure_tab.grid_columnconfigure(0, weight=1)
        measure_tab.grid_rowconfigure(0, weight=1)
        
        # A read-only CTkTextbox to display DAQ values (like your status tab)
        self.daq_text_box = ctk.CTkTextbox(measure_tab, state="disabled")
        self.daq_text_box.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # A frame to hold the "Read DAQ" button
        measure_button_frame = ctk.CTkFrame(measure_tab)
        measure_button_frame.grid(row=1, column=0, sticky="ew")
        
        # Button that triggers reading from the DAQ
        self.read_daq_button = ctk.CTkButton(
            measure_button_frame,
            text="Read DAQ",
            command=self._read_all_daq_channels
        )
        self.read_daq_button.pack(side="left", padx=5, pady=5)

        # Compact error display
        self.error_display = ctk.CTkTextbox(
            inner_frame, 
            height=100,  # Reduced height
            state="disabled"
        )
        self.error_display.grid(row=2, column=0, sticky="ew", pady=(2, 0))

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

    def _read_all_daq_channels(self):
        """
        Lists all available AI channels on the DAQ device,
        reads averaged voltage for each channel, and displays them in the text box.
        """
        if not self.daq:
            self._update_measurement_text("No DAQ object found.")
            return

        channels = self.daq.list_ai_channels()
        if not channels:
            self._update_measurement_text("No DAQ channels found or DAQ not connected.")
            return

        readings = self.daq.read_power_in_mW(channels=channels, samples_per_channel=10)
        if readings is None:
            self._update_measurement_text("Failed to read from DAQ or DAQ not connected.")
            return

        # Normalize to list for consistent processing
        if isinstance(readings, float):
            readings = [readings]  # wrap float in list if only one channel

        # Build text output
        lines = []
        for ch_name, voltage in zip(channels, readings):
            lines.append(f"{ch_name} -> {voltage:.3f} mW")

        self._update_measurement_text("\n".join(lines))
    
    def _update_measurement_text(self, text):
        """Helper to safely update the CTkTextbox in read-only style."""
        self.daq_text_box.configure(state="normal")
        self.daq_text_box.delete("1.0", "end")
        self.daq_text_box.insert("1.0", text)
        self.daq_text_box.configure(state="disabled")

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
            print(AppData.default_json_grid)
            # grid_config = json.loads(self.custom_grid.export_paths_json())
            grid_config = AppData.default_json_grid
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
                # messagebox.showinfo("Phase Application", result_message)
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
                # config = self.custom_grid.export_paths_json()
                config_json = json.dumps(phase_grid_config)
                apply_grid_mapping(self.qontrol, config_json, self.grid_size)
            except Exception as e:
                self._show_error(f"Device update failed: {str(e)}")        

            return phase_grid_config
            
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
        delay = 0.5
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