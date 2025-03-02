# app/gui/main_window.py
from app.imports import *
import customtkinter as ctk
import tkinter.messagebox as messagebox
import app.gui.widgets as widgets
import app.gui.window1 as window1
from app.gui.window1 import Window1Content  # Import the Window1Content widget
from app.gui.window2 import Window2Content  # Import the Window2Content widget
from app.gui.window3 import Window3Content  # Import the Window3Content widget
from app.devices.qontrol_device import QontrolDevice  # Your QontrolDevice class
import app.utils
from app.utils.utils import importfunc
from app.utils.appdata import AppData   # Import the AppData class
# from app.utils import utils            # This module contains apply_phase

class MainWindow(ctk.CTk):
    def __init__(self, qontrol, thorlabs, config):
        super().__init__()
        self.qontrol = qontrol
        self.thorlabs = thorlabs
        self.config = config

        self.current_content = None  # Important: so we can check it safely switch tabs
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{screen_width}x{screen_height}+-10+-5")

        # Create an AppData instance with the desired number of channels.
        self.appdata = AppData(n_channels=0)

        # Main frame with left and right panels.
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(expand=True, fill="both")

        # Left panel for control widgets.
        self.left_panel = ctk.CTkFrame(self.main_frame, width=300)
        self.left_panel.grid(row=0, column=0, sticky="nsew")

        # Right panel for main application content.
        self.right_panel = ctk.CTkFrame(self.main_frame)
        self.right_panel.grid(row=0, column=1, sticky="nsew")

        self.main_frame.grid_columnconfigure(0, weight=0)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Add control widgets to the left panel.
        self.device_control = widgets.DeviceControlWidget(
            master=self.left_panel,
            connect_command=self.connect_devices,
            disconnect_command=self.disconnect_devices
        )
        self.device_control.pack(anchor="nw", padx=10, pady=(10, 5), fill="x")

        self.app_control = widgets.AppControlWidget(
            master=self.left_panel,
            import_command=self.import_data,
            export_command=self.export_data,
            mesh_change_command=self.mesh_changed,
            config=self.config
        )
        self.app_control.pack(anchor="nw", padx=10, pady=(5, 5), fill="x")
        
        self.windowSelection = widgets.WindowSelectionWidget(
            master=self.left_panel,
            change_command=self.window_changed
        )
        self.windowSelection.pack(anchor="nw", padx=10, pady=(5, 10), fill="x")
 
        # Initially, load the content for Window 1.
        self.load_window_content("Window 1")
        
        # Connect devices after widgets are built.
        self.after(200, self.connect_devices)

    def window_changed(self, selected_window):
        self.load_window_content(selected_window)

    def load_window_content(self, window_name):
        
        # If the current content is Window3, save all NxN data
        if isinstance(self.current_content, Window3Content) and self.current_content.winfo_exists():
            self.current_content.save_all_tabs()
    
        # Clear the right panel.
        for widget in self.right_panel.winfo_children():
            widget.destroy()
            
        if window_name == "Window 1":
            # Retrieve the mesh size from the OptionMenu.
            mesh_size = self.app_control.mesh_optionmenu.get()
            # Create the Window1Content and store it.
            self.current_content = Window1Content(
                self.right_panel,
                channel=0,
                fit="Linear",
                IOconfig="Config1",
                app=self.appdata,
                qontrol=self.qontrol,
                thorlabs = self.thorlabs,
                grid_size=mesh_size
            )
            self.current_content.pack(expand=True, fill="both", padx=10, pady=10)
        elif window_name == "Window 2":
            # Create the Window2Content (which integrates the Qontrol control panel)
            self.current_content = Window2Content(
                self.right_panel,
                channel=0,
                fit="Linear",
                IOconfig="Config1",
                app=self.appdata,
                qontrol=self.qontrol,
            )
            self.current_content.pack(expand=True, fill="both", padx=10, pady=10)
        elif window_name == "Window 3":
            # Retrieve the mesh size from the OptionMenu.
            mesh_size = self.app_control.mesh_optionmenu.get()
            self.current_content = Window3Content(  # Use Window3Content, even if it's similar to Window1Content
                self.right_panel,
                channel=0,
                fit="Linear",
                IOconfig="Config1",
                app=self.appdata,
                qontrol=self.qontrol,
                grid_size=mesh_size
            )            
            self.current_content.pack(expand=True, fill="both", padx=10, pady=10)
            
        else:
            placeholder = ctk.CTkLabel(self.right_panel, text=f"{window_name} content not implemented yet.")
            placeholder.pack(expand=True, fill="both", padx=10, pady=10)

    # def connect_devices(self):
    #     if self.qontrol:
    #         # Check if the device is already connected (assuming self.qontrol.device is set when connected)
    #         if hasattr(self.qontrol, "device") and self.qontrol.device is not None:
    #             # Already connected; update device info only.
    #             params = self.qontrol.params
    #             params["Global Current Limit"] = self.qontrol.globalcurrrentlimit
    #             self.device_control.update_device_info(params)
    #         else:
    #             # Not connected yet, so connect.
    #             self.qontrol.connect()
    #             params = self.qontrol.params
    #             params["Global Current Limit"] = self.qontrol.globalcurrrentlimit
    #             self.device_control.update_device_info(params)
    #     else:
    #         messagebox.showerror("Connection Error", "No Qontrol device available!")

    # def disconnect_devices(self):
    #     if self.qontrol:
    #         self.qontrol.disconnect()
    #     self.device_control.update_device_info({})

    def connect_devices(self):
        # Handle Qontrol connection should be connected by default
        if self.qontrol:
            if hasattr(self.qontrol, "device") and self.qontrol.device is not None:
                params = self.qontrol.params
                params["Global Current Limit"] = self.qontrol.globalcurrrentlimit
                self.device_control.update_device_info(params, "qontrol")
            else:
                # Not connected yet, so connect.
                self.qontrol.connect()
                print("Re-Connecting to Qontrol device...")
                if self.qontrol.device:  # Only update if connection succeeded
                    params = self.qontrol.params
                    params["Global Current Limit"] = self.qontrol.globalcurrrentlimit
                    self.device_control.update_device_info(params, "qontrol")

        # Handle Thorlabs connection should be connected by default
        if self.thorlabs:  # Add thorlabs connection handling
            if hasattr(self.thorlabs, "device") and self.thorlabs.device is not None:
                params = self.thorlabs.params
                # params["Global Current Limit"] = self.qontrol.globalcurrrentlimit
                self.device_control.update_device_info(params, "thorlabs")
            else:
                self.thorlabs.connect()
                print("Re-Connecting to Thorlabs device...")
                if self.thorlabs.device:  # Only update if connection succeeded
                    params = self.thorlabs.params
                    # params["Global Current Limit"] = self.qontrol.globalcurrrentlimit
                    self.device_control.update_device_info(params, "thorlabs")

    def disconnect_devices(self):
        if self.qontrol:
            self.qontrol.disconnect()
        if self.thorlabs:
            self.thorlabs.disconnect()
        # Clear both device displays
        self.device_control.update_device_info(None, "qontrol")
        self.device_control.update_device_info(None, "thorlabs")
    
    def import_data(self):
        # Call the import function to update the appdata.
        importfunc(self.appdata)
        # For demonstration, print one of the imported matrices.
        print("Updated with Pickle file:", self.appdata.phiphase2list)
        messagebox.showinfo("Import", "Data imported successfully!")

    def export_data(self):
        messagebox.showinfo("Export", "Export function triggered.")

    def mesh_changed(self, new_mesh_size):
        print("Mesh size changed to:", new_mesh_size)
    
        # If the current tab is Window 1 => update
        if isinstance(self.current_content, Window1Content):
            self.current_content.update_grid(new_mesh_size)
    
        # If the current tab is Window 3 => update
        if isinstance(self.current_content, Window3Content):
            self.current_content.update_grid(new_mesh_size)

if __name__ == "__main__":
    qontrol_device = QontrolDevice(config={"globalcurrrentlimit"})
    app = MainWindow(qontrol=qontrol_device, thorlabs=None, config={})
    app.mainloop()
