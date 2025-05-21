import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
import serial.tools.list_ports

# Add project root (e.g., where the "app" folder is located)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.devices.switch_device import Switch

class SwitchGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Serial Switch Controller")
        self.switch = None

        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.grid()

        # Port selection
        ttk.Label(frame, text="Serial Port:").grid(row=0, column=0, sticky="e")
        self.port_combo = ttk.Combobox(frame, values=self._list_serial_ports(), state="readonly")
        self.port_combo.grid(row=0, column=1)
        self.port_combo.bind("<<ComboboxSelected>>", self._on_port_selected)

        # Channel selection
        ttk.Label(frame, text="Channel (0-64):").grid(row=1, column=0, sticky="e")
        self.channel_spin = ttk.Spinbox(frame, from_=0, to=64, width=5)
        self.channel_spin.grid(row=1, column=1, sticky="w")

        # Set button
        self.set_btn = ttk.Button(frame, text="Set Channel", command=self.set_channel, state="disabled")
        self.set_btn.grid(row=2, column=0, columnspan=2, pady=5)

        # Get button
        self.get_btn = ttk.Button(frame, text="Get Current Channel", command=self.get_channel, state="disabled")
        self.get_btn.grid(row=3, column=0, columnspan=2)

        # Result label
         
        self.result_label = ttk.Label(frame, text="")
        self.result_label.grid(row=4, column=0, columnspan=2, pady=10)

    def _list_serial_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]

    def _on_port_selected(self, event):
        port = self.port_combo.get()
        self.switch = Switch(port)
        self.set_btn.config(state="normal")
        self.get_btn.config(state="normal")

    def set_channel(self):
        try:
            channel = int(self.channel_spin.get())
            if self.switch.set_channel(channel):
                self.result_label.config(text=f"Channel set to {channel}")
            else:
                self.result_label.config(text="Failed to set channel")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set channel:\n{e}")

    def get_channel(self):
        try:
            current = self.switch.get_channel()
            if current is not None:
                self.result_label.config(text=f"Current channel: {current}")
            else:
                self.result_label.config(text="Failed to read channel")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get channel:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = SwitchGUI(root)
    root.mainloop()

