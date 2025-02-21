# app/gui/window1.py
from app.imports import *
import customtkinter as ctk
from app.utils import grid  # Import the grid module
import tkinter.simpledialog as simpledialog

class Window1Content(ctk.CTkFrame):
    def __init__(self, master, channel, fit, IOconfig, app, qontrol, grid_size="8x8", **kwargs):
        super().__init__(master, **kwargs)
        self.channel = channel
        self.fit = fit
        self.IOconfig = IOconfig
        self.app = app
        self.qontrol = qontrol  # Store the Qontrol device here.
        self.grid_size = grid_size
        
        # Create a main content frame with some outer padding.
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent", border_width=0)
        self.content_frame.pack(expand=True, fill="both", padx=5, pady=5)
        
        # Left: grid container (for displaying the grid)
        self.grid_container = ctk.CTkFrame(self.content_frame, fg_color="transparent", border_width=0, corner_radius=0)
        self.grid_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Right: a frame to hold import/export buttons and a text box.
        self.right_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent", border_width=0, corner_radius=0)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Place the import/export button frame at the top of the right frame.
        self.import_export_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent", border_width=0)
        self.import_export_frame.pack(fill="x", padx=5, pady=(5,2))
        self.export_button = ctk.CTkButton(
            self.import_export_frame, text="Export", command=self.export_paths,
            height=20, width=60, font=("TkDefaultFont", 10)
        )
        self.export_button.pack(side="left", padx=1)
        self.import_button = ctk.CTkButton(
            self.import_export_frame, text="Import", command=self.import_paths,
            height=20, width=60, font=("TkDefaultFont", 10)
        )
        self.import_button.pack(side="left", padx=1)
        
        # Place the text box below the buttons.
        self.selected_paths_display = ctk.CTkTextbox(self.right_frame, width=200, height=80)
        self.selected_paths_display.pack(fill="x", padx=5, pady=(2,5))
        
        # (You might have additional buttons; for example, a "Print Values" button.)
        self.print_button = ctk.CTkButton(
            self.right_frame, text="Print Values", command=self.print_input_values,
            height=20, width=60, font=("TkDefaultFont", 10)
        )
        self.print_button.pack(fill="x", padx=5, pady=(2,5))
        
        # Increase the grid container's relative size.
        self.content_frame.grid_columnconfigure(0, weight=9)  # More space for the grid.
        self.content_frame.grid_columnconfigure(1, weight=1)  # Less space for the right panel.
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Build the grid using the initial grid_size.
        self.build_grid(self.grid_size)
    
    def build_grid(self, grid_size):
        try:
            n = int(grid_size.split('x')[0])
        except Exception as e:
            print("Error parsing grid size, defaulting to 8x8:", e)
            n = 8
        scale = 0.8 if n == 12 else 1.0
        self.custom_grid = grid.Example(self.grid_container, grid_n=n, scale=scale)
        self.custom_grid.pack(expand=True, fill="both")
        self.custom_grid.selection_callback = self.update_selected_paths
    
    def update_selected_paths(self, selected_str):
        self.selected_paths_display.delete("0.0", "end")
        self.selected_paths_display.insert("0.0", selected_str)
    
    def export_paths(self):
        json_str = self.custom_grid.export_paths_json()
        self.selected_paths_display.delete("0.0", "end")
        self.selected_paths_display.insert("0.0", json_str)
    
    def import_paths(self):
        json_str = simpledialog.askstring("Import Paths", "Enter JSON for selected paths:")
        if json_str:
            self.custom_grid.import_paths_json(json_str)
            self.custom_grid.update_selection()
    
    def update_grid(self, new_grid_size):
        cover = ctk.CTkFrame(self.grid_container, fg_color="grey16", border_width=0)
        cover.place(relwidth=1, relheight=1)
        self.grid_container.update_idletasks()
        for widget in self.grid_container.winfo_children():
            widget.destroy()
        self.build_grid(new_grid_size)
        cover.destroy()
    
    def print_input_values(self):
        """Prints the theta and phi values for each input box."""
        if not hasattr(self.custom_grid, 'input_boxes'):
            print("No input boxes found.")
            return
        for cross_label, widget_dict in self.custom_grid.input_boxes.items():
            theta_value = widget_dict['theta_entry'].get()
            phi_value = widget_dict['phi_entry'].get()
            print(f"Cross {cross_label}: theta = {theta_value}, phi = {phi_value}")

# calibrationplotX