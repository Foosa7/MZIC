#!/usr/bin/env python3
"""
mqtt_tkinter_gui.py

A simple Tkinter-based GUI that communicates with a Raspberry Pi running the
Qontrol MQTT gateway (which uses your unmodified qontrol.py library).

This GUI:
  - Provides input fields for channel number and current value.
  - Publishes JSON commands to set a channel’s current and to request a status update.
  - Subscribes to topics for status updates and error logs.
  - Displays the received voltage/current readings and error messages.

Topics used (should match the gateway on the Pi):
  - qontrol/command/set_current    (expects payload like: {"channel": 0, "current": 2.5})
  - qontrol/command/get_status     (no payload required)
  - qontrol/status                 (status JSON is published by the Pi)
  - qontrol/errors                 (error log JSON is published by the Pi)
"""

import tkinter as tk
from tkinter import ttk
import json
import paho.mqtt.client as mqtt

# MQTT broker settings – here we use the public HiveMQ broker.
BROKER = "broker.hivemq.com"
PORT = 1883

# MQTT topics (must match those used on the Raspberry Pi)
TOPIC_CMD_SET_CURRENT = "qontrol/command/set_current"
TOPIC_CMD_GET_STATUS  = "qontrol/command/get_status"
TOPIC_STATUS          = "qontrol/status"
TOPIC_ERRORS          = "qontrol/errors"


class MQTTGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Qontrol MQTT GUI")
        self.geometry("600x500")
        self.create_widgets()
        self.setup_mqtt()

    def create_widgets(self):
        # --- Controls Frame ---
        control_frame = tk.Frame(self)
        control_frame.pack(pady=10)
        
        tk.Label(control_frame, text="Channel:").grid(row=0, column=0, padx=5)
        self.channel_entry = tk.Entry(control_frame, width=5)
        self.channel_entry.grid(row=0, column=1, padx=5)
        
        tk.Label(control_frame, text="Current (mA):").grid(row=0, column=2, padx=5)
        self.current_entry = tk.Entry(control_frame, width=10)
        self.current_entry.grid(row=0, column=3, padx=5)
        
        self.set_button = tk.Button(control_frame, text="Set Current", command=self.set_current)
        self.set_button.grid(row=0, column=4, padx=5)
        
        self.get_status_button = tk.Button(control_frame, text="Get Status", command=self.get_status)
        self.get_status_button.grid(row=0, column=5, padx=5)
        
        # --- Status Frame ---
        status_frame = tk.LabelFrame(self, text="Status")
        status_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.status_text = tk.Text(status_frame, height=10)
        self.status_text.pack(side="left", fill="both", expand=True)
        
        status_scroll = tk.Scrollbar(status_frame, command=self.status_text.yview)
        status_scroll.pack(side="right", fill="y")
        self.status_text.config(yscrollcommand=status_scroll.set)
        
        # --- Errors Frame ---
        error_frame = tk.LabelFrame(self, text="Errors")
        error_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.error_text = tk.Text(error_frame, height=5, fg="red")
        self.error_text.pack(side="left", fill="both", expand=True)
        
        error_scroll = tk.Scrollbar(error_frame, command=self.error_text.yview)
        error_scroll.pack(side="right", fill="y")
        self.error_text.config(yscrollcommand=error_scroll.set)

    def setup_mqtt(self):
        # Create the MQTT client.
        self.mqtt_client = mqtt.Client()
        # Set our GUI instance into userdata so callbacks can update the GUI.
        self.mqtt_client.user_data_set({"app": self})
        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.on_message = on_message

        try:
            self.mqtt_client.connect(BROKER, PORT, 60)
        except Exception as e:
            self.append_status("Failed to connect to MQTT broker: " + str(e))
        # Use loop_start() so the MQTT client runs in a background thread.
        self.mqtt_client.loop_start()

    def set_current(self):
        """Send a JSON command to set the current on a given channel."""
        try:
            channel = int(self.channel_entry.get())
            current = float(self.current_entry.get())
        except ValueError:
            self.append_status("Invalid input for channel or current.")
            return
        payload = {"channel": channel, "current": current}
        self.mqtt_client.publish(TOPIC_CMD_SET_CURRENT, json.dumps(payload))
        self.append_status(f"Published set_current: {payload}")

    def get_status(self):
        """Send a JSON command to request device status."""
        self.mqtt_client.publish(TOPIC_CMD_GET_STATUS, json.dumps({}))
        self.append_status("Published get_status command.")

    def handle_message(self, topic, payload):
        """Handle incoming MQTT messages by updating the GUI."""
        if topic == TOPIC_STATUS:
            self.append_status("Status: " + payload)
        elif topic == TOPIC_ERRORS:
            self.append_error("Errors: " + payload)

    def append_status(self, message):
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)

    def append_error(self, message):
        self.error_text.insert(tk.END, message + "\n")
        self.error_text.see(tk.END)


# MQTT callback functions.
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code " + str(rc))
    # Subscribe to status and error topics.
    client.subscribe([(TOPIC_STATUS, 0), (TOPIC_ERRORS, 0)])


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode("utf-8")
    # Retrieve the GUI instance from userdata.
    app = userdata.get("app")
    if app:
        # Use after() to ensure thread-safe update of the GUI.
        app.after(0, app.handle_message, topic, payload)


if __name__ == "__main__":
    app = MQTTGUI()
    app.mainloop()
