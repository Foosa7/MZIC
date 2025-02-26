# app/gui/window2.py

import io
import tkinter.messagebox
import customtkinter as ctk
import tkinter as tk
from contextlib import redirect_stdout
from app.devices.qontrol_device import QontrolDevice

class Window2Content(ctk.CTkFrame):
    def __init__(self, master, channel=0, fit="Linear", IOconfig="Config1", app=None, qontrol=None, **kwargs):
        super().__init__(master, **kwargs)
        
        # Validate and store device reference
        if not isinstance(qontrol, QontrolDevice):
            raise ValueError("Valid QontrolDevice instance required")
        self.qontrol_device = qontrol
        
        # Configure grid layout
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(4, weight=1)  # Allow expansion
        
        # --- UI Elements ---
        # Channel Input
        self.channel_label = ctk.CTkLabel(self, text="Channel:")
        self.channel_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.channel_entry = ctk.CTkEntry(self, width=100)
        self.channel_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.channel_entry.insert(0, str(channel))
        
        # Current Input
        self.current_label = ctk.CTkLabel(self, text="Current (mA):")
        self.current_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.current_entry = ctk.CTkEntry(self, width=100)
        self.current_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        self.current_entry.insert(0, "0")
        
        # Action Buttons
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        
        self.set_button = ctk.CTkButton(self.button_frame, text="Set Values", command=self.set_values)
        self.set_button.pack(side="left", padx=5, pady=5)
        
        self.status_button = ctk.CTkButton(self.button_frame, text="Full Status", command=self.show_full_status)
        self.status_button.pack(side="left", padx=5, pady=5)
        
        self.voltage_button = ctk.CTkButton(self.button_frame, text="All Voltages", command=self.show_all_voltages)
        self.voltage_button.pack(side="left", padx=5, pady=5)

        # System Info Display
        self.info_text = ctk.CTkTextbox(self, wrap=tk.WORD, height=150)
        self.info_text.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.info_text.configure(state="disabled")
        
        # Error Display
        self.error_text = ctk.CTkTextbox(self, wrap=tk.WORD, height=100)
        self.error_text.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.error_text.configure(state="disabled")
        
        # Input monitoring setup
        self.after_id = None
        self._setup_input_monitoring()

    def _setup_input_monitoring(self):
        """Configure input tracking with debounced checks"""
        self.channel_var = tk.StringVar()
        self.current_var = tk.StringVar()
        
        self.channel_entry.configure(textvariable=self.channel_var)
        self.current_entry.configure(textvariable=self.current_var)
        
        for var in [self.channel_var, self.current_var]:
            var.trace_add("write", lambda *_: self._schedule_system_check())

    def _schedule_system_check(self):
        """Manage delayed system checks"""
        if self.after_id:
            self.after_cancel(self.after_id)
        self.after_id = self.after(50, self._update_system_info)

    def _update_system_info(self):
        """Refresh both status and error displays"""
        try:
            # Update error display
            self._capture_device_output(self.qontrol_device.show_errors, self.error_text)
            
            # Update general status
            self._capture_device_output(self.qontrol_device.show_status, self.info_text)
            
        except Exception as e:
            self._display_error(f"System check failed: {str(e)}")
        finally:
            self.after_id = None

    def _capture_device_output(self, device_func, text_widget):
        """Capture printed output from device functions"""
        f = io.StringIO()
        with redirect_stdout(f):
            try:
                device_func()
            except Exception as e:
                print(f"Error executing command: {str(e)}")
        output = f.getvalue()
        
        text_widget.configure(state="normal")
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", output)
        text_widget.configure(state="disabled")

    def show_full_status(self):
        """Display complete device status"""
        self._capture_device_output(self.qontrol_device.show_status, self.info_text)

    def show_all_voltages(self):
        """Display all voltage readings"""
        self._capture_device_output(self.qontrol_device.show_voltages, self.info_text)

    def set_values(self):
        """Set current on specified channel"""
        try:
            channel = int(self.channel_entry.get())
            current = float(self.current_entry.get())
            self.qontrol_device.set_current(channel, current)
            self._display_temp_message(f"Set Ch{channel} to {current} mA")
        except ValueError:
            tkinter.messagebox.showerror("Input Error", "Invalid numeric values")
        except Exception as e:
            self._display_error(str(e))

    def _display_temp_message(self, message):
        """Show temporary status message"""
        self.info_text.configure(state="normal")
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert("1.0", message)
        self.info_text.configure(state="disabled")
        self.after(3000, self._update_system_info)  # Revert after 3 seconds

    def _display_error(self, message):
        """Show error message in both displays"""
        self.error_text.configure(state="normal")
        self.error_text.delete("1.0", tk.END)
        self.error_text.insert("1.0", message)
        self.error_text.configure(state="disabled")
        tkinter.messagebox.showerror("Operation Failed", message)

if __name__ == "__main__":
    # Test implementation
    q_device = QontrolDevice(config={"global_current_limit"})
    if q_device.connect():
        app = ctk.CTk()
        app.title("Qontrol Control Panel")
        Window2Content(app, qontrol=q_device).pack(expand=True, fill="both")
        app.mainloop()
    else:
        print("Failed to connect to Qontrol device")
