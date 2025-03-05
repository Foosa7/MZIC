# app/gui/window1.py
from app.imports import *

from app.utils.appdata import AppData
import io
from contextlib import redirect_stdout
import customtkinter as ctk
from app.utils import grid
from app.utils.qontrol.qmapper8x8 import create_label_mapping, apply_grid_mapping
from collections import defaultdict
from typing import Dict, Any

class Window1Content(ctk.CTkFrame):
    def __init__(self, master, channel, fit, IOconfig, app, qontrol, thorlabs, grid_size="8x8", **kwargs):
        super().__init__(master, **kwargs)
        self.qontrol = qontrol
        self.thorlabs = thorlabs
        self.grid_size = grid_size
        self.after_id = None
        self.control_panel = None  
        self.resistance_params: Dict[int, Dict[str, Any]] = {}
  

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
        self._create_calibration_controls()
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
            ("Apply", self._apply_config),
            ("Clear", self._clear_grid),
            ("Status", self._show_full_status)
        ]
        # Smaller buttons with compact layout
        for col, (text, cmd) in enumerate(controls):
            btn = ctk.CTkButton(
                btn_frame, 
                text=text, 
                command=cmd,
                width=50,  # Reduced width to fit 5 buttons
                height=24,
                font=ctk.CTkFont(size=11)
            )
            btn.grid(row=0, column=col, padx=1, sticky="nsew")
            btn_frame.grid_columnconfigure(col, weight=1)

        
        # Compact notebook for displays
        notebook = ctk.CTkTabview(inner_frame, height=180)  # Fixed height
        notebook.grid(row=1, column=0, sticky="nsew", pady=(2, 0))
        inner_frame.grid_columnconfigure(0, weight=1)
        
        # Status tab
        self.status_display = ctk.CTkTextbox(notebook.add("Status"), state="disabled")
        self.status_display.pack(fill="both", expand=True)
        
        # Mapping tab
        self.mapping_display = ctk.CTkTextbox(notebook.add("Mapping"))
        self.mapping_display.pack(fill="both", expand=True)
        
        # Compact error display
        self.error_display = ctk.CTkTextbox(
            inner_frame, 
            height=60,  # Reduced height
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

    def _update_device(self):
        """Update Qontrol device with current values"""
        try:
            config = self.custom_grid.export_paths_json()
            apply_grid_mapping(self.qontrol, config, self.grid_size)
        except Exception as e:
            self._show_error(f"Device update failed: {str(e)}")

    def _export_config(self):
        """Export current configuration"""
        try:
            return self.custom_grid.export_paths_json()
        except Exception as e:
            self._show_error(f"Export failed: {str(e)}")

    def _import_config(self):
        """Import configuration from JSON"""
        dialog = ctk.CTkInputDialog(text="Paste JSON configuration:", title="Import Config")
        json_str = dialog.get_input()
        
        if json_str:
            try:
                self.custom_grid.import_paths_json(json_str)
                self._update_device()
            except Exception as e:
                self._show_error(f"Invalid config: {str(e)}")

    def _handle_selection_update(self, event):
        """Event-driven update handler"""
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
        """Clear all selections and reset the grid"""
        # try:
            # Clear all selections
        for path in self.custom_grid.paths:
            if path.line_id in self.custom_grid.selected_paths:
                self.custom_grid.canvas.itemconfig(path.line_id, fill="white")
        self.custom_grid.selected_paths.clear()
        
        # Clear all input boxes
        for cross_label in list(self.custom_grid.input_boxes.keys()):
            self.custom_grid.delete_input_boxes(cross_label)
        
        # Reset last selection
        self.custom_grid.last_selection = {"cross": None, "arm": None}
        AppData.update_last_selection(None, None)
        
        # Update the selection display
        self.custom_grid.update_selection()
        
        # Trigger the selection updated event
        self.custom_grid.event_generate("<<SelectionUpdated>>")
        
        # print("Grid cleared successfully")
        # except Exception as e:
            # self._show_error(f"Failed to clear grid: {str(e)}")
            # print                    

    def _apply_config(self):
        """Force apply current configuration"""
        self._update_device()

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

    def _create_calibration_controls(self):
        """Add calibration section to control panel"""
        calibration_frame = ctk.CTkFrame(self.control_panel)
        calibration_frame.pack(pady=10, fill='x')
        
        # Channel selection display
        self.current_channel_label = ctk.CTkLabel(calibration_frame, text="No channel selected")
        self.current_channel_label.pack(pady=5)
        
        # Theta/Phi selector
        # self.channel_type_var = ctk.StringVar(value="theta")
        # ctk.CTkRadioButton(calibration_frame, text="Theta", variable=self.channel_type_var, value="theta").pack(side='left')
        # ctk.CTkRadioButton(calibration_frame, text="Phi", variable=self.channel_type_var, value="phi").pack(side='left', padx=10)

        self.channel_type_var = ctk.StringVar(value="theta")
        ctk.CTkRadioButton(
            calibration_frame, 
            text="θ",  # Changed from "Theta"
            variable=self.channel_type_var, 
            value="theta",
            font=ctk.CTkFont(family="Arial", size=14)  # Ensures symbol support
        ).pack(side='left')
        ctk.CTkRadioButton(
            calibration_frame, 
            text="φ",  # Changed from "Phi"
            variable=self.channel_type_var, 
            value="phi",
            font=ctk.CTkFont(family="Arial", size=14)
        ).pack(side='left', padx=10)



        # Calibration button
        ctk.CTkButton(calibration_frame, 
                     text="Characterize Resistance", 
                     command=self._run_calibration).pack(pady=10)

    def _get_current_channels(self, event=None):
        """Get theta/phi channels for current selection"""
        current = AppData.get_last_selection()
        if not current or 'cross' not in current:
            return None, None
        
        label_map = create_label_mapping(8)
        theta_ch, phi_ch = label_map.get(current['cross'], (None, None))
        print(f"θ{theta_ch}, φ{phi_ch}")

        return theta_ch, phi_ch

    def _run_calibration(self):
        """Run resistance characterization on selected channel"""
        try:
            theta_ch, phi_ch = self._get_current_channels()
            channel_type = self.channel_type_var.get()
            target_channel = theta_ch if channel_type == "theta" else phi_ch
            
            if target_channel is None:
                raise ValueError("No valid channel selected")
                
            # Run characterization
            self._characterize_resistance(target_channel)
            
            # Update UI
            self._update_calibration_display(target_channel)
            
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


        # Calculate differential resistance (dV/dI)
        # resistance = 3*a*currents**2 + c  # Derivative of cubic fit
        # Calculate resistance using the cubic+linear model

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
        # print(f"Resistance Range: {np.min(resistance):.2f}Ω - {np.max(resistance):.2f}Ω")
        # print(f"Resistance @ Max Current: {resistance[-1]:.2f}Ω")
  
    # def _update_calibration_display(self, channel):
    #     """Update UI with calibration results"""
    #     params = self.resistance_params.get(channel)
    #     if not hasattr(self, 'resistance_params'):
    #         self.resistance_params = {}
    #     # if not params:
    #         return
            
    #     # Update channel info
    #     self.current_channel_label.configure(
    #         text=f"Channel {channel} ({'Theta' if channel == self._get_current_channels()[0] else 'Phi'})"
    #     )
        
    #     # Update plots
    #     fig = self._create_calibration_plot(params)
    #     self._display_plot(fig)

    # def _display_plot(self, fig):
    #     """Display matplotlib plot in GUI"""
    #     buf = io.BytesIO()
    #     fig.savefig(buf, format='png')
    #     buf.seek(0)
        
    #     # Update image display (assuming you have an image widget)
    #     # self.calibration_image.configure(light_image=Image.open(buf))
    #     plt.close(fig)

    def _update_calibration_display(self, channel):
        """Update UI with calibration results"""
        params = self.resistance_params.get(channel)
        if not params:
            return
        
        # Get current channel type from radio buttons
        channel_type = self.channel_type_var.get()
        
        # Generate plot with channel context
        fig = self._create_calibration_plot(params, channel_type, channel)  # Add missing args
        self._display_plot(fig, channel)


    def _create_calibration_plot(self, params, channel_type, target_channel):
        """Generate styled resistance characterization plot"""
        current = AppData.get_last_selection()
        label_map = create_label_mapping(8)
        channel_type = self.channel_type_var.get()
        channel_symbol = "θ" if channel_type == "theta" else "φ"

        # Get both channels but only show selected one
        theta_ch, phi_ch = label_map.get(current['cross'], (None, None))
        
        # Create plot with dark theme
        fig, ax = plt.subplots(figsize=(8, 5))
        fig.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#363636')
        
        # Plot data points and fit curve
        ax.plot(params['currents'], params['voltages'], 
            'o', color='white', markersize=6, label='Measured Data')
        x_fit = np.linspace(min(params['currents']), max(params['currents']), 100)
        y_fit = params['a']*x_fit**3 + params['c']*x_fit + params['d']
        ax.plot(x_fit, y_fit, color='#ff4b4b', linewidth=2.5, label='Cubic Fit')

        # # Dynamic title based on selected channel type
        # title_str = (f"Resistance Characterization: {current['cross']} "
        #             f"Characterizing {channel_type.capitalize()} Channel: {target_channel}")
        title_str = (f"Resistance Characterization of {current['cross']}:{channel_symbol} at Channel {target_channel}")

        ax.set_title(title_str, color='white', fontsize=12, pad=20)
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

        return fig

    def _display_plot(self, fig, channel):
        """Display matplotlib plot in a popup window"""
        # Create popup window
        plot_window = ctk.CTkToplevel(self)
        # plot_window.title(f"Channel {channel} Calibration Results")
        plot_window.title(f"Channel {channel} Calibration Results")  
        plot_window.geometry("800x600")
        
        # Convert plot to image
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        img = Image.open(buf)
        
        # Create CTk image and label
        ctk_image = ctk.CTkImage(
            light_image=img,
            dark_image=img,
            size=(750, 550)
        )
        
        label = ctk.CTkLabel(plot_window, image=ctk_image, text="")
        label.pack(padx=10, pady=10)
        
        # Add close button
        close_btn = ctk.CTkButton(
            plot_window, 
            text="Close", 
            command=plot_window.destroy
        )
        close_btn.pack(pady=5)
        
        plt.close(fig)
