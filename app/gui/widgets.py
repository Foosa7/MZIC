# app/gui/widgets.py

from app.imports import *

class DeviceControlWidget(ctk.CTkFrame):
    def __init__(self, master, connect_command=None, disconnect_command=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        
        # --- Header Section with a Light Grey Fill ---
        self.header_frame = ctk.CTkFrame(
            self,

            fg_color="#4c4c4c",  # Light grey fill
            border_width=0,      # No border needed now since it's a filled area
            corner_radius=4
        )
        self.header_frame.pack(fill="x", padx=10, pady=(10, 5), anchor="center")
        
        self.status_label = ctk.CTkLabel(
            self.header_frame,
            text="Device Control",
            anchor="center",
            font=("TkDefaultFont", 13, "bold"),
            justify="center"
        )
        self.status_label.pack(fill="x", padx=5, pady=5)
        
        # --- Information Display Section ---
        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        self.device_label = ctk.CTkLabel(self.info_frame, text="Device: -", anchor="w")
        self.firmware_label = ctk.CTkLabel(self.info_frame, text="Firmware: -", anchor="w")
        self.channels_label = ctk.CTkLabel(self.info_frame, text="Channels: -", anchor="w")
        self.current_limit_label = ctk.CTkLabel(self.info_frame, text="Current limit: -", anchor="w")

        # Thorlabs Device Parameters 
        self.thorlabs_model_label = ctk.CTkLabel(self.info_frame, text="Thorlabs Model: -", anchor="w")
        # self.thorlabs_serial_label = ctk.CTkLabel(self.info_frame, text="Serial: -", anchor="w")
        # self.thorlabs_wavelength_label = ctk.CTkLabel(self.info_frame, text="Wavelength: - nm", anchor="w")
        # self.thorlabs_power_label = ctk.CTkLabel(self.info_frame, text="Power Range: -", anchor="w")

        # Packing order
        self.device_label.pack(fill="x", padx=10, pady=(0, 2))
        self.firmware_label.pack(fill="x", padx=10, pady=(0, 2))
        self.channels_label.pack(fill="x", padx=10, pady=(0, 2))
        self.current_limit_label.pack(fill="x", padx=10, pady=(0, 10))  # Extra spacing
        
        # Thorlabs labels
        self.thorlabs_model_label.pack(fill="x", padx=10, pady=(0, 2))
        # self.thorlabs_serial_label.pack(fill="x", padx=10, pady=(0, 2))
        # self.thorlabs_wavelength_label.pack(fill="x", padx=10, pady=(0, 2))
        # self.thorlabs_power_label.pack(fill="x", padx=10, pady=(0, 2))


        self.device_label.pack(fill="x", padx=10, pady=(0, 2))
        self.firmware_label.pack(fill="x", padx=10, pady=(0, 2))
        self.channels_label.pack(fill="x", padx=10, pady=(0, 2))
        self.current_limit_label.pack(fill="x", padx=10, pady=(0, 2))
        self.thorlabs_model_label.pack(fill="x", padx=10, pady=(0, 2))
        # --- Button Section ---
        # self.button_holder_frame = ctk.CTkFrame(self, fg_color="transparent", border_width=0)
        # self.button_holder_frame.pack(side="top", anchor="center", padx=10, pady=(5, 10))
        
        # self.buttons_frame = ctk.CTkFrame(self.button_holder_frame, fg_color="transparent", border_width=0)
        # self.buttons_frame.pack(padx=10, pady=10)
        # self.buttons_frame.grid_columnconfigure(0, weight=1)
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        self.connect_button = ctk.CTkButton(
            self.button_frame,
            text="Connect Devices",
            command=connect_command,
            height=30
        )
        self.connect_button.pack(fill="x", pady=2) #grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.disconnect_button = ctk.CTkButton(
            self.button_frame,
            text="Disconnect Devices",
            command=disconnect_command,
            height=30
        )
        self.disconnect_button.pack(fill="x", pady=2) #grid(row=1, column=0, padx=10, pady=10, sticky="ew")
    

    def update_device_info(self, params, device_type):
        """Handle Qontrol and multiple Thorlabs updates with type checking"""
        # Extract device index for thorlabs devices (thorlabs, thorlabs1, thorlabs2, etc.)
        
        if not device_type:
            self._clear_all_labels()
            return
        
        # If we're updating Qontrol device
        if params and device_type == "qontrol":
            # Update Qontrol parameters
            self.device_label.configure(text=f"Device: Qontroller '{params.get('Device id', '-')}'")
            self.firmware_label.configure(text=f"Firmware: {params.get('Firmware', '-')}")
            self.channels_label.configure(text=f"Channels: {params.get('Available channels', '-')}")
            self.current_limit_label.configure(text=f"Current limit: {params.get('Global Current Limit', '-')} mA")    
        
        # If we're updating (one or more) Thorlabs device(s)
        elif params and device_type.startswith("thorlabs"):
            
            device_index = device_type[8:]  # Extract index number if present
            
            if device_index == "":
                self.thorlabs_model_label.configure(
                    text=f"Thorlabs 0 (SN: {params.get('Serial', '-')})"    
                )
            else:
                attr_name = f"thorlabs_model_label{device_index}"
                if not hasattr(self, attr_name):
                    label = ctk.CTkLabel(self.info_frame, anchor="w")
                    setattr(self, attr_name, label)
                    label.pack(fill="x", padx=10, pady=(0,2))
                label = getattr(self, attr_name)
                label.configure(
                    text=f"Thorlabs {device_index} (SN: {params.get('Serial', '-')})"    
                )
                
        elif device_type.startswith("thorlabs"):
            device_index = device_type[8:]
            
            if device_index == "":
                self.thorlabs_model_label.configure(text="Thorlabs Model: -")
            else:
                attr_name = f"thorlabs_model_label{device_index}"
                if hasattr(self, attr_name):
                    getattr(self, attr_name).configure(text=f"Thorlabs {device_index} Model: -")
                
    def _clear_all_labels(self):
        self.device_label.configure(text="Device: -")
        self.firmware_label.configure(text="Firmware: -")
        self.channels_label.configure(text="Channels: -")
        self.current_limit_label.configure(text="Current limit: -")
        self.thorlabs_model_label.configure(text="Thorlabs Model: -")
        
        for attr_name in dir(self):
            if attr_name.startswith("thorlabs_model_label") and attr_name != "thorlabs_model_label":
                get_attr(self, attr_name).configure(text=f"Thorlabs {attr_name[19:]} Model: -")

    
class AppControlWidget(ctk.CTkFrame):
    def __init__(self, master, import_command=None, export_command=None, 
                mesh_change_command=None, config=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.config = config or {}  # Store the config
        
        # --- Header Section ---
        self.header_frame = ctk.CTkFrame(
            self,
            fg_color="#4c4c4c",
            border_width=0,
            corner_radius=4
        )
        self.header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        self.header_label = ctk.CTkLabel(
            self.header_frame,
            text="App Control",
            font=("TkDefaultFont", 13, "bold")
        )
        self.header_label.pack(padx=5, pady=5)
        
        # --- Mesh Size Selection ---
        self.mesh_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.mesh_frame.pack(fill="x", padx=10, pady=5)

        # Get options from config with fallback
        mesh_options = self.config.get("options", ["6x6", "8x8", "12x12"])
        
        self.mesh_label = ctk.CTkLabel(self.mesh_frame, text="Mesh Size:")
        self.mesh_label.pack(side="left", padx=(0, 5))
        
        self.mesh_optionmenu = ctk.CTkOptionMenu(
            self.mesh_frame,
            values=mesh_options,
            command=mesh_change_command
        )
        # Set default from config or first option
        if mesh_options:
            default_mesh = self.config.get("default_mesh", mesh_options[1])
            self.mesh_optionmenu.set(default_mesh)
        self.mesh_optionmenu.pack(side="left")
        
        # --- Import/Export Buttons ---
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        self.import_button = ctk.CTkButton(
            self.button_frame,
            text="Import",
            command=import_command
        )
        self.import_button.pack(fill="x", pady=2)
        
        self.export_button = ctk.CTkButton(
            self.button_frame,
            text="Export",
            command=export_command
        )
        self.export_button.pack(fill="x", pady=2)

class WindowSelectionWidget(ctk.CTkFrame):
    def __init__(self, master, change_command=None, *args, **kwargs):
        """
        A widget to select the window.
        
        Parameters:
            master: Parent widget.
            change_command (callable): Callback called with the new window string
                                       when the selection changes.
        """
        super().__init__(master, *args, **kwargs)
        
        # --- Header Section with Light Grey Fill ---
        self.header_frame = ctk.CTkFrame(
            self,
            fg_color="#4c4c4c",  # Darker grey for the header (adjust as needed)
            border_width=0,
            corner_radius=4
        )
        self.header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        self.header_label = ctk.CTkLabel(
            self.header_frame,
            text="Window Selection",
            anchor="center",
            font=("TkDefaultFont", 13, "bold"),
            justify="center"
        )
        self.header_label.pack(fill="x", padx=5, pady=5)
        
        # --- Radio Button Section (Vertical Layout) ---
        self.radio_var = ctk.StringVar(value="Window 1")
        self.radio_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.radio_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        # Create radio buttons labeled as windows.
        self.radio1 = ctk.CTkRadioButton(
            self.radio_frame,
            text="Diagram",
            variable=self.radio_var,
            value="Window 1",
            command=self.on_radio_change
        )
        self.radio1.pack(side="top", fill="x", padx=5, pady=5)
        
        self.radio2 = ctk.CTkRadioButton(
            self.radio_frame,
            text="Calibrate",
            variable=self.radio_var,
            value="Window 2",
            command=self.on_radio_change
        )
        self.radio2.pack(side="top", fill="x", padx=5, pady=5)
        
        self.radio3 = ctk.CTkRadioButton(
            self.radio_frame,
            text="Unitary",
            variable=self.radio_var,
            value="Window 3",
            command=self.on_radio_change
        )
        self.radio3.pack(side="top", fill="x", padx=5, pady=5)
        
        # self.radio4 = ctk.CTkRadioButton(
        #     self.radio_frame,
        #     text="Window 4",
        #     variable=self.radio_var,
        #     value="Window 4",
        #     command=self.on_radio_change
        # )
        # self.radio4.pack(side="top", fill="x", padx=5, pady=5)
        
        self.change_command = change_command

    def on_radio_change(self):
        if self.change_command:
            self.change_command(self.radio_var.get())
    
    def get_selected_window(self):
        return self.radio_var.get()

class PlotWidget(ctk.CTkFrame):
    def __init__(self, master, title="Plot", *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        
        # Configure dark theme colors
        self.bg_color = "#2b2b2b"
        self.text_color = "white"
        self.line_color = "#3CBA54"
        
        # Create figure and axis
        self.fig = Figure(figsize=(6, 4), dpi=100, facecolor=self.bg_color)
        self.ax = self.fig.add_subplot(111)
        
        # Set plot styling
        self._configure_plot_style()
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        
        # Create toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()
        
        # Layout
        self.toolbar.pack(side=ctk.TOP, fill=ctk.X)
        self.canvas.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

    def _configure_plot_style(self):
        """Configure matplotlib style to match dark theme"""
        self.ax.set_facecolor(self.bg_color)
        self.ax.tick_params(axis='x', colors=self.text_color)
        self.ax.tick_params(axis='y', colors=self.text_color)
        self.ax.xaxis.label.set_color(self.text_color)
        self.ax.yaxis.label.set_color(self.text_color)
        self.ax.title.set_color(self.text_color)
        
        for spine in self.ax.spines.values():
            spine.set_color(self.text_color)

    def plot_calibration(self, channel, xdata, ydata, fit_params):
        """Plot calibration data from imported parameters"""
        self.ax.clear()
        
        # Plot raw data
        self.ax.plot(xdata, ydata, 'o', color=self.line_color, label='Measured Data')
        
        # Generate fit line
        fit_x = np.linspace(min(xdata), max(xdata), 300)
        fit_y = fit_params['fitfunc'](fit_x)
        
        # Plot fit
        self.ax.plot(fit_x, fit_y, '--', color='red', label='Fitted Curve')
        
        # Add labels and legend
        self.ax.set_xlabel("Heating Power (mW)", color=self.text_color)
        self.ax.set_ylabel("Optical Power (mW)", color=self.text_color)
        self.ax.set_title(f"Channel {channel} Calibration", color=self.text_color)
        self.ax.legend(facecolor=self.bg_color, edgecolor=self.text_color)
        
        # Redraw canvas
        self._configure_plot_style()
        self.canvas.draw()

    def clear_plot(self):
        """Clear the current plot"""
        self.ax.clear()
        self._configure_plot_style()
        self.canvas.draw()


class CalibrationControlWidget(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.create_calibration_controls()

    def create_calibration_controls(self):
        """Add calibration section with separate buttons"""
        self.calibration_frame = ctk.CTkFrame(self)
        self.calibration_frame.pack(pady=10, fill='x', expand=True)

        # Channel selection display
        self.current_channel_label = ctk.CTkLabel(self.calibration_frame, text="No channel selected")
        self.current_channel_label.pack(pady=0)

        # Create container frame for side-by-side layout
        io_config_frame = ctk.CTkFrame(self.calibration_frame, fg_color="transparent")
        io_config_frame.pack(pady=5, fill='x')

        # Theta/Phi selector
        self.channel_type_var = ctk.StringVar(value="theta")
        type_frame = ctk.CTkFrame(io_config_frame, fg_color="transparent")
        type_frame.pack(side='left', padx=(10,0), expand=True)
        ctk.CTkRadioButton(type_frame, text="θ", variable=self.channel_type_var, value="theta").pack(side='left')
        ctk.CTkRadioButton(type_frame, text="φ", variable=self.channel_type_var, value="phi").pack(side='left', padx=5)

        # Configure grid columns for equal spacing
        io_config_frame.grid_columnconfigure(0, weight=1)
        io_config_frame.grid_columnconfigure(1, weight=1)

        # Calibration buttons
        btn_frame = ctk.CTkFrame(self.calibration_frame, fg_color="transparent")
        btn_frame.pack(pady=10, fill='x')

        # Configure grid columns
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)