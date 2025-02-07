# app/gui/widgets.py

from app.imports import *
import tkinter as tk
import customtkinter as ctk

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
        
        self.device_label.pack(fill="x", padx=10, pady=(0, 2))
        self.firmware_label.pack(fill="x", padx=10, pady=(0, 2))
        self.channels_label.pack(fill="x", padx=10, pady=(0, 2))
        self.current_limit_label.pack(fill="x", padx=10, pady=(0, 2))
        
        # --- Button Section ---
        self.button_holder_frame = ctk.CTkFrame(self, fg_color="transparent", border_width=0)
        self.button_holder_frame.pack(side="top", anchor="center", padx=10, pady=(5, 10))
        
        self.buttons_frame = ctk.CTkFrame(self.button_holder_frame, fg_color="transparent", border_width=0)
        self.buttons_frame.pack(padx=10, pady=10)
        self.buttons_frame.grid_columnconfigure(0, weight=1)
        
        self.connect_button = ctk.CTkButton(
            self.buttons_frame,
            text="Connect Devices",
            command=connect_command,
            height=30
        )
        self.connect_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        self.disconnect_button = ctk.CTkButton(
            self.buttons_frame,
            text="Disconnect Devices",
            command=disconnect_command,
            height=30
        )
        self.disconnect_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
    
    def update_device_info(self, params):
        if params:
            device_id = params.get("Device id", "Disconnected")
            firmware = params.get("Firmware", "-")
            channels = params.get("Available channels", "-")
            current_limit = params.get("Global Current Limit", "-")
            
            self.device_label.configure(text=f"Device: Qontroller '{device_id}'")
            self.firmware_label.configure(text=f"Firmware: {firmware}")
            self.channels_label.configure(text=f"Channels: {channels}")
            self.current_limit_label.configure(text=f"Current limit: {current_limit} mA")
        else:
            self.status_label.configure(text="Device Control")
            self.device_label.configure(text="Device: -")
            self.firmware_label.configure(text="Firmware: -")
            self.channels_label.configure(text="Channels: -")
            self.current_limit_label.configure(text="Current limit: -")


class AppControlWidget(ctk.CTkFrame): 
    def __init__(self, master, import_command=None, export_command=None, mesh_change_command=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        
        # --- Header Section with a Light Grey Fill ---
        self.header_frame = ctk.CTkFrame(
            self,
            fg_color="#4c4c4c",  # Light grey fill for the header
            border_width=0,
            corner_radius=4
        )
        self.header_frame.pack(fill="x", padx=10, pady=(10, 5), anchor="center")
        
        self.header_label = ctk.CTkLabel(
            self.header_frame,
            text="App Control",
            anchor="center",
            font=("TkDefaultFont", 13, "bold"),
            justify="center"
        )
        self.header_label.pack(fill="x", padx=5, pady=5)
        
        # --- Mesh Size Selection Section ---
        self.mesh_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.mesh_frame.pack(fill="x", padx=10, pady=(5, 5))
        
        self.mesh_label = ctk.CTkLabel(self.mesh_frame, text="Mesh Size:", anchor="w")
        self.mesh_label.pack(side="left", padx=(0, 5))
        
        # Pass the mesh_change_command to be called when the option changes.
        self.mesh_optionmenu = ctk.CTkOptionMenu(
            self.mesh_frame, 
            values=["6x6", "8x8", "12x12"],
            command=mesh_change_command  # This callback will be set by the MainWindow.
        )
        self.mesh_optionmenu.set("8x8")
        self.mesh_optionmenu.pack(side="left", padx=(0, 5))
        
        # --- Button Section ---
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        self.import_button = ctk.CTkButton(
            self.button_frame,
            text="Import",
            command=import_command,
            height=30
        )
        self.import_button.pack(fill="x", padx=10, pady=5)
        
        self.export_button = ctk.CTkButton(
            self.button_frame,
            text="Export",
            command=export_command,
            height=30
        )
        self.export_button.pack(fill="x", padx=10, pady=5)

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
            font=("TkDefaultFont", 14, "bold"),
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
            text="Window 3",
            variable=self.radio_var,
            value="Window 3",
            command=self.on_radio_change
        )
        self.radio3.pack(side="top", fill="x", padx=5, pady=5)
        
        self.radio4 = ctk.CTkRadioButton(
            self.radio_frame,
            text="Window 4",
            variable=self.radio_var,
            value="Window 4",
            command=self.on_radio_change
        )
        self.radio4.pack(side="top", fill="x", padx=5, pady=5)
        
        self.change_command = change_command

    def on_radio_change(self):
        if self.change_command:
            self.change_command(self.radio_var.get())
    
    def get_selected_window(self):
        return self.radio_var.get()
