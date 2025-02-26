# app/gui/window1.py
import io
from contextlib import redirect_stdout
import customtkinter as ctk
from app.utils import grid
from app.utils.qmapper8x8 import create_label_mapping, apply_grid_mapping
from collections import defaultdict

class Window1Content(ctk.CTkFrame):
    def __init__(self, master, channel, fit, IOconfig, app, qontrol, grid_size="8x8", **kwargs):
        super().__init__(master, **kwargs)
        self.qontrol = qontrol
        self.grid_size = grid_size
        self.after_id = None
        
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
        self._start_status_updates()

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
            ("Status", self._show_full_status)
        ]

        # Smaller buttons with compact layout
        for col, (text, cmd) in enumerate(controls):
            btn = ctk.CTkButton(
                btn_frame, 
                text=text, 
                command=cmd,
                width=60,  # Reduced width
                height=24,  # Reduced height
                font=ctk.CTkFont(size=11)  # Smaller font
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
        self.after(1000, self._start_status_updates)

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


    def _create_status_displays(self):
        """Status displays are now integrated in control panel"""
        pass

    def build_grid(self, grid_size):
        """Initialize the grid display"""
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

    def _attach_grid_listeners(self):
        """Attach event listeners to grid inputs"""
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


    def update_grid(self, new_grid_size):
        cover = ctk.CTkFrame(self.grid_container, fg_color="grey16", border_width=0)
        cover.place(relwidth=1, relheight=1)
        self.grid_container.update_idletasks()
        for widget in self.grid_container.winfo_children():
            widget.destroy()
        self.build_grid(new_grid_size)
        cover.destroy()
                    

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
