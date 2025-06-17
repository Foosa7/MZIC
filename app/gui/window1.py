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
from app.utils.gui import grid
from app.utils.qontrol.qmapper8x8 import create_label_mapping, apply_grid_mapping
from collections import defaultdict
from typing import Dict, Any
from scipy import optimize
from app.utils.calibrate.calibrate import CalibrationUtils
from app.utils.gui.plot_utils import PlotUtils
from app.utils.utils import create_zero_config, calculate_current_for_phase
from PIL import Image
import matplotlib.pyplot as plt

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
        self.calibration_utils = CalibrationUtils()
        self.plot_utils = PlotUtils()

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
        self._create_status_displays()
        
        # Initial setup
        self.build_grid(self.grid_size)
        self.custom_grid.master = self.grid_container  # Explicit parent assignment
        self._start_status_updates()
        self._setup_event_bindings()

        self.selected_unit = "uW"  # Default unit for power measurement

        # self._initialize_live_graph() # Initialize the live graph



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
        
        # Compact inner frame
        inner_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        inner_frame.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        inner_frame.grid_rowconfigure(1, weight=1)

        # Compact button row
        btn_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 2))

        controls = [
            ("Import", self._import_config),
            ("Export", self._export_config),
            ("Current", self._apply_config),
            ("Clear", self._clear_grid),
            ("R", self.characterize_resistance),
            ("P", self.characterize_phase),
            ("Phase", self.apply_phase_new),
            ("Save Cal", self.export_calibration_data),  # Add these two buttons
            ("Load Cal", self.import_calibration_data)
        ]

        for col in range(9):
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
        notebook = ctk.CTkTabview(inner_frame, height=180, width=300)  # Fixed height, width
        notebook.grid_propagate(False)
        notebook.grid(row=1, column=0, sticky="nsew", pady=(2, 0))
        inner_frame.grid_columnconfigure(0, weight=1)

        ### Graph tab ###
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

        ### Mapping tab ###
        self.mapping_display = ctk.CTkTextbox(notebook.add("Mapping"))
        self.mapping_display.pack(fill="both", expand=True)
        
        ### Status tab ###
        self.status_display = ctk.CTkTextbox(notebook.add("Status"), state="disabled")
        self.status_display.pack(fill="both", expand=True)
                # Compact error display in inner_frame
        self.error_display = ctk.CTkTextbox(inner_frame, height=100, state="disabled")
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
        self.replot_current_selection()
        print(f"Current selection: {current['cross']}-{current['arm']}")


    def _create_status_displays(self):
        """Status displays are now integrated in control panel"""
        pass


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
            lines.append(f"{ch_name} -> {voltage:.3f} {self.selected_unit}")

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
                readings.append(f"Thorlabs {i} -> {power:.3f} {self.selected_unit}")
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
        self.custom_grid.pack(fill="both", expand=True) #
        self._attach_grid_listeners()
        
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

    def _update_device(self):
        """Update Qontrol device with current values"""
        try:
            config = self.custom_grid.export_paths_json()
            apply_grid_mapping(self.qontrol, config, self.grid_size)
        except Exception as e:
            self._show_error(f"Device update failed: {str(e)}")

    def _export_config(self):
        """Export current configuration to a JSON file."""
        try:
            config_str = self.custom_grid.export_paths_json()
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
            for path in self.custom_grid.paths:
                if path.line_id in self.custom_grid.selected_paths:
                    self.custom_grid.canvas.itemconfig(path.line_id, fill="white")
            self.custom_grid.selected_paths.clear()
            
            for cross_label in list(self.custom_grid.input_boxes.keys()):
                self.custom_grid.delete_input_boxes(cross_label)
            
            self.custom_grid.cross_selected_count.clear()
            self.custom_grid.last_selection = {"cross": None, "arm": None}
            AppData.update_last_selection(None, None)
            
            self.custom_grid.update_selection()
            self.custom_grid.event_generate("<<SelectionUpdated>>")
            
            zero_config = create_zero_config(self.grid_size)
            apply_grid_mapping(self.qontrol, zero_config, self.grid_size)
            print("Grid cleared and all values set to zero")
            self._capture_output(self.qontrol.show_status, self.status_display)

        except Exception as e:
            self._show_error(f"Failed to clear grid: {str(e)}")
            print(f"Error in clear grid: {e}")

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
            grid_config = json.loads(self.custom_grid.export_paths_json())
            print(grid_config)
            if not grid_config:
                self._show_error("No grid configuration found W1")
                return
                
            label_map = create_label_mapping(8)
            phase_grid_config = copy.deepcopy(grid_config)
            applied_channels = []
            failed_channels = []
            
            for cross_label, data in grid_config.items():
                if cross_label not in label_map:
                    continue
                    
                theta_ch, phi_ch = label_map[cross_label]
                theta_val = data.get("theta", "0")
                phi_val = data.get("phi", "0")

                if theta_ch is not None and theta_val:
                    try:
                        theta_float = float(theta_val)
                        current_theta = calculate_current_for_phase(self.app, theta_ch, theta_float, "cross", "bar")
                        if current_theta is not None:
                            current_theta = round(current_theta, 5)
                            phase_grid_config[cross_label]["theta"] = str(current_theta)
                            applied_channels.append(f"{cross_label}:θ = {current_theta:.5f} mA")
                        else:
                            failed_channels.append(f"{cross_label}:θ (no calibration)")
                    except Exception as e:
                        failed_channels.append(f"{cross_label}:θ ({str(e)})")

                if phi_ch is not None and phi_val:
                    try:
                        phi_float = float(phi_val)
                        current_phi = calculate_current_for_phase(self.app, phi_ch, phi_float, "cross", "bar")
                        if current_phi is not None:
                            current_phi = round(current_phi, 5)
                            phase_grid_config[cross_label]["phi"] = str(current_phi)
                            applied_channels.append(f"{cross_label}:φ = {current_phi:.5f} mA")
                        else:
                            failed_channels.append(f"{cross_label}:φ (no calibration)")
                    except Exception as e:
                        failed_channels.append(f"{cross_label}:φ ({str(e)})")
            
            self.phase_grid_config = phase_grid_config
            
            if failed_channels:
                result_message = f"Failed to apply to {len(failed_channels)} channels"
                print(result_message)
                
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

    def _show_full_status(self):
        """Display detailed device status"""
        self._capture_output(self.qontrol.show_status, self.status_display)

    def _show_error(self, message):
        """Display error message in compact dialog"""
        self.error_display.configure(state="normal")
        self.error_display.delete("1.0", "end")
        self.error_display.insert("1.0", message)
        self.error_display.configure(state="disabled")
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Error")
        dialog.geometry("300x80")
        
        ctk.CTkLabel(dialog, text=message, wraplength=280).pack(pady=5)
        ctk.CTkButton(dialog, text="OK", command=dialog.destroy, width=60).pack(pady=5)

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
        print(f"Current selection: {current['cross']}-{current['arm']}")

        return theta_ch, phi_ch

    def characterize_resistance(self):
        """Handle resistance characterization button click"""
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
                
            # Execute resistance characterization
            result = self.calibration_utils.characterize_resistance(
                self.qontrol, 
                target_channel
            )
            
            # Store results
            self.resistance_params[target_channel] = result

            # --- Add this block ---
            label_map = create_label_mapping(8)  # Use your grid size if not 8
            channel_to_label = {}
            for label, (theta_ch, phi_ch) in label_map.items():
                channel_to_label[theta_ch] = f"{label}_theta"
                channel_to_label[phi_ch] = f"{label}_phi"
            label = channel_to_label.get(target_channel, str(target_channel))
            from app.utils.appdata import AppData
            AppData.update_resistance_calibration(label, {
                "pin": target_channel,
                "resistance_params": {
                    "a": float(result['a']),
                    "c": float(result['c']),
                    "d": float(result['d']),
                    "rmin": float(result['rmin']),
                    "rmax": float(result['rmax']),
                    "alpha": float(result['alpha'])
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
            self.mapping_display.insert("end", f"Alpha: {result['alpha']:.4f}\n")
            self.mapping_display.configure(state="disabled")
            
            # Generate and display plot
            current = AppData.get_last_selection()
            fig = self.plot_utils.plot_resistance(
                result['currents'],
                result['voltages'],
                [result['a'], result['c'], result['d']],  # Resistance params
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
                img = Image.open(buf)

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
            
            print(f"Running phase calibration for channel {target_channel} ({io_config})")
            
            # Execute phase characterization
            result = self.calibration_utils.characterize_phase(
                self.qontrol,
                self.thorlabs,
                target_channel,
                io_config
            )
            
            # Store results
            self.phase_params[target_channel] = result

            # --- Add this block ---
            label_map = create_label_mapping(8)  # Use your grid size if not 8
            channel_to_label = {}
            for label, (theta_ch, phi_ch) in label_map.items():
                channel_to_label[theta_ch] = f"{label}_theta"
                channel_to_label[phi_ch] = f"{label}_phi"
            label = channel_to_label.get(target_channel, str(target_channel))
            AppData.update_phase_calibration(label, {
                "pin": target_channel,
                "phase_params": {
                    "io_config": result['io_config'],
                    "amplitude": float(result['amp']),
                    "frequency": float(result['omega']/(2*np.pi)),
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
            self.mapping_display.insert("end", f"Frequency: {result['omega']/(2*np.pi):.4f} Hz\n")
            self.mapping_display.insert("end", f"Phase: {result['phase']:.4f} rad\n")
            self.mapping_display.configure(state="disabled")
            
            # Generate and display plot
            fig = self.plot_utils.plot_phase(
                result['currents'],
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

        label_map = create_label_mapping(8)  # Or use self.grid_size if dynamic
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
