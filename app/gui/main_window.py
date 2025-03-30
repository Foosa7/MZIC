# app/gui/main_window.py
from app.imports import *
import customtkinter as ctk
import tkinter.messagebox as messagebox
import app.gui.widgets as widgets
import app.gui.window1 as window1
from app.gui.widgets import PhaseShifterSelectionWidget

from app.gui.window1 import Window1Content  # Import the Window1Content widget
from app.gui.window2 import Window2Content  # Import the Window2Content widget
from app.gui.window3 import Window3Content  # Import the Window3Content widget
from app.devices.qontrol_device import QontrolDevice  # Your QontrolDevice class
import app.utils
from app.utils.utils import importfunc
from app.utils.appdata import AppData   # Import the AppData class
# from app.utils import utils            # This module contains apply_phase

class MainWindow(ctk.CTk):
    def __init__(self, qontrol, thorlabs, daq, config):
        super().__init__()
        self.qontrol = qontrol
        self.thorlabs = thorlabs
        self.config = config
        self.daq = daq

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
 
        # Add calibration controls
        self.calibration_control = PhaseShifterSelectionWidget(self.left_panel)
        self.calibration_control.pack(anchor="nw", padx=10, pady=(5, 10), fill="x")

        # # Add other widgets...
        # self.windowSelection.pack(anchor="nw", padx=10, pady=(5, 10), fill="x")
        
        # Initially, load the content for Window 1.
        self.load_window_content("Window 1")
        
        # Connect devices after widgets are built.
        self.after(200, self.connect_devices)

    def window_changed(self, selected_window):
        self.load_window_content(selected_window)

    def load_window_content(self, window_name):
        
        # If the current content is Window3, save all NxN data
        if isinstance(self.current_content, Window3Content) and self.current_content.winfo_exists():
            self.current_content.handle_all_tabs(operation='save')
    
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
                daq = self.daq,
                grid_size=mesh_size,
                phase_selector=self.calibration_control,  # Pass the existing widget

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
                daq = self.daq,
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
                print("[INFO][Qontrol] Re-Connecting to device...")
                if self.qontrol.device:  # Only update if connection succeeded
                    params = self.qontrol.params
                    params["Global Current Limit"] = self.qontrol.globalcurrrentlimit
                    self.device_control.update_device_info(params, "qontrol")


        # Handle Thorlabs connection(s)
        if isinstance(self.thorlabs, list):
            # Multiple Thorlabs devices
            for i, thorlabs_device in enumerate(self.thorlabs):
                device_id = f"thorlabs{i}" if i > 0 else "thorlabs"
                if hasattr(thorlabs_device, "device") and thorlabs_device.device is not None:
                    params = thorlabs_device.params
                    self.device_control.update_device_info(params, device_id)
                else:
                    thorlabs_device.connect()
                    print(f"[INFO][Thorlabs] Re-Connecting to device {i}...")
                    if thorlabs_device.device:  # Only update if connection succeeded
                        params = thorlabs_device.params
                        self.device_control.update_device_info(params, device_id)
        elif self.thorlabs:  # Single Thorlabs device
            if hasattr(self.thorlabs, "device") and self.thorlabs.device is not None:
                params = self.thorlabs.params
                self.device_control.update_device_info(params, "thorlabs")
            else:
                self.thorlabs.connect()
                print("[INFO][Thorlabs] Re-Connecting to Thorlabs device...")
                if self.thorlabs.device:  # Only update if connection succeeded
                    params = self.thorlabs.params
                    self.device_control.update_device_info(params, "thorlabs")


        # Handle DAQ connection
        if self.daq:
            if self.daq._is_connected:
                print("[INFO][DAQ] Already connected.")
                # Build a small status dict
                status_dict = {
                    "DAQ Device": self.daq.device_name,
                    "Channels": ", ".join(self.daq.list_ai_channels() or [])
                }
                self.device_control.update_device_info(status_dict, "daq")
            else:
                if self.daq.connect():
                    print("[INFO][DAQ] Connected to device.")
                    status_dict = {
                        "DAQ Device": self.daq.device_name,
                        "Channels": ", ".join(self.daq.list_ai_channels() or [])
                    }
                    self.device_control.update_device_info(status_dict, "daq")
                else:
                    print("[INFO][DAQ] Connection failed.")
                    self.device_control.update_device_info(None, "daq")

    def disconnect_devices(self):
        if self.qontrol:
            self.qontrol.disconnect()

        # DAQ
        if self.daq:
            self.daq.disconnect()
            self.device_control.update_device_info(None, "daq")        

        # Handle disconnecting Thorlabs device(s)
        if isinstance(self.thorlabs, list):
            # Multiple Thorlabs devices
            for i, thorlabs_device in enumerate(self.thorlabs):
                thorlabs_device.disconnect()
                device_id = f"thorlabs{i}" if i > 0 else "thorlabs"
                self.device_control.update_device_info(None, device_id)
        elif self.thorlabs:
            # Single Thorlabs device
            self.thorlabs.disconnect()
            self.device_control.update_device_info(None, "thorlabs")
        
        # Clear Qontrol display
        self.device_control.update_device_info(None, "qontrol")


    
    def import_data(self):
        # Call the import function to update the appdata.
        importfunc(self.appdata)
        # For demonstration, print one of the imported matrices.
        print("[INFO] Updated with Pickle file:", self.appdata.caliparamlist_lincub_cross[1])
        # messagebox.showinfo("Import", "Data imported successfully!")

    def export_data(self):
        print("[INFO] Export function triggered.")

    def mesh_changed(self, new_mesh_size):
        print("[INFO] Mesh size changed to:", new_mesh_size)
    
        # If the current tab is Window 1 => update
        if isinstance(self.current_content, Window1Content):
            self.current_content.update_grid(new_mesh_size)
    
        # If the current tab is Window 3 => update
        if isinstance(self.current_content, Window3Content):
            self.current_content.update_grid(new_mesh_size)

if __name__ == "__main__":
    qontrol_device = QontrolDevice(config={"globalcurrrentlimit"})
    app = MainWindow(qontrol=qontrol_device, thorlabs=None, daq=None, config={})
    app.mainloop()
