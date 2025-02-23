#!/usr/bin/env python3
import customtkinter as ctk
import tkinter as tk
import tkinter.messagebox
from qontrol import QXOutput  # Ensure your qontrol.py is in your PYTHONPATH

class QontrolGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Fresh Qontrol GUI")
        self.geometry("400x350")
        
        # --- Connect to the Qontrol Device ---
        # IMPORTANT: Change "COM12" to the appropriate serial port for your system.
        try:
            self.qx = QXOutput(serial_port_name="COM12", response_timeout=0.1)
        except Exception as e:
            tkinter.messagebox.showerror("Connection Error", f"Error connecting to Qontrol device:\n{e}")
            self.destroy()
            return
        
        # --- Build GUI Elements ---
        # Input frame for channel and current.
        input_frame = ctk.CTkFrame(self)
        input_frame.pack(pady=10, padx=10, fill="x")
        
        # Channel input.
        self.channel_label = ctk.CTkLabel(input_frame, text="Channel:")
        self.channel_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.channel_entry = ctk.CTkEntry(input_frame, width=80)
        self.channel_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.channel_entry.insert(0, "0")
        
        # Current input.
        self.current_label = ctk.CTkLabel(input_frame, text="Current (mA):")
        self.current_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.current_entry = ctk.CTkEntry(input_frame, width=80)
        self.current_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.current_entry.insert(0, "0")
        
        # Buttons frame.
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(pady=10, padx=10, fill="x")
        
        # Set Current button.
        self.set_button = ctk.CTkButton(button_frame, text="Set Current", command=self.set_current)
        self.set_button.grid(row=0, column=0, padx=5, pady=5)
        
        # Read Voltage button.
        self.read_button = ctk.CTkButton(button_frame, text="Read Voltage", command=self.read_voltage)
        self.read_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Read Errors button.
        self.error_button = ctk.CTkButton(button_frame, text="Read Errors", command=self.read_errors)
        self.error_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Output label.
        self.output_label = ctk.CTkLabel(self, text="Output will appear here.", wraplength=380)
        self.output_label.pack(pady=10)
    
    def set_current(self):
        try:
            channel = int(self.channel_entry.get())
            current = float(self.current_entry.get())
            print("Full-scale current (IFULL):", self.qx.ifull)
        except ValueError:
            tkinter.messagebox.showerror("Input Error", "Please enter valid numbers for channel and current.")
            return
        
        try:
            # Use "I" as the parameter for current.
            self.qx.set_value(channel, "I", current)
            self.output_label.configure(text=f"Channel {channel} set to {current} mA")
        except Exception as e:
            tkinter.messagebox.showerror("Error", f"Error setting current for channel {channel}:\n{e}")
    
    def read_voltage(self):
        try:
            channel = int(self.channel_entry.get())
        except ValueError:
            tkinter.messagebox.showerror("Input Error", "Please enter a valid channel number.")
            return
        
        try:
            voltage = self.qx.get_value(channel, "V")
            self.output_label.configure(text=f"Channel {channel} voltage: {voltage} V")
        except Exception as e:
            tkinter.messagebox.showerror("Error", f"Error reading voltage on channel {channel}:\n{e}")
    
    def read_errors(self):
        try:
            # Filter the log for error entries.
            errors = [entry for entry in self.qx.log if entry.get("type") == "err"]
            if errors:
                error_text = "\n".join(
                    [f"Time: {e['timestamp']}, Code: {e['id']}, Channel: {e['ch']}, Desc: {e['desc']}" 
                     for e in errors]
                )
            else:
                error_text = "No errors reported."
            self.output_label.configure(text=error_text)
        except Exception as e:
            tkinter.messagebox.showerror("Error", f"Error reading error log:\n{e}")

if __name__ == "__main__":
    app = QontrolGUI()
    app.mainloop()
