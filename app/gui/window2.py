# app/gui/window2.py

from app.imports import *
import tkinter as tk
import customtkinter as ctk
import numpy as np
import sympy as sp

class Window2Content(ctk.CTkFrame):
    def __init__(self, master, channel=0, fit="Linear", IOconfig="Config1", app=None, *args, **kwargs):
        """
        A widget that displays the content for Window 1.
        
        Parameters:
          master: The parent widget (will be the right panel).
          channel: Channel number.
          fit: Fit type (e.g., "Linear").
          IOconfig: IO configuration (e.g., "Config1").
          app: The main application object with required attributes.
        """
        super().__init__(master, *args, **kwargs)
        if app is None:
            raise ValueError("An app object must be provided to access settings.")
        self.app = app
        self.currentchannel = channel
        self.currentIOconfig = IOconfig
        self.currentfit = fit
        self.fitnames = np.array(["Linear", "Linear+cubic"])
        self.currentfit_name = self.fitnames[self.app.fit_func.index(self.currentfit)]
        self.fit_index = self.app.fit_func.index(self.currentfit)
        self.IOconfig_index = self.app.IOconfig_options.index(self.currentIOconfig)
        
        self.calpararrays = [
            [self.app.caliparamlist_lin_cross, self.app.caliparamlist_lin_bar],
            [self.app.caliparamlist_lincub_cross, self.app.caliparamlist_lincub_bar]
        ]
        self.currentarray = self.calpararrays[self.fit_index][self.IOconfig_index]
        self.currentsettings = self.currentarray[self.currentchannel]
        
        # Create a header label.
        header_text = f"Window 1 - Settings for Channel {self.currentchannel}"
        self.header = ctk.CTkLabel(self, text=header_text,
                                   font=ctk.CTkFont(size=16, weight="bold"))
        self.header.pack(pady=10)
        
        # Display some dummy information.
        if self.currentsettings != "Null":
            self.A = self.currentsettings["amp"]
            self.d = self.currentsettings["offset"]
            self.c = self.currentsettings["phase"]
            self.b = self.currentsettings["omega"]
            self.visibility = self.A / self.d
            if self.currentfit == self.app.fit_func[0]:
                self.R = self.app.linear_resistance_list[self.currentchannel]
                self.P_pi = abs((np.pi - self.c) / self.b)
                self.mod_period = 2 * np.pi / self.b
                self.pi_PS_current = 1000 * np.sqrt(self.P_pi / (self.R * 1000))
            elif self.currentfit == self.app.fit_func[1]:
                I = sp.symbols('I')
                self.R0 = self.app.resistance_parameter_list[self.currentchannel][1]
                self.alpha = self.app.resistance_parameter_list[self.currentchannel][0] / self.app.resistance_parameter_list[self.currentchannel][1]
                self.P_pi = abs((np.pi - self.c) / self.b) / 1000
                self.mod_period = 2 * np.pi / self.b
                eq = sp.Eq(self.P_pi / self.R0, I**2 + self.alpha * I**4)
                solutions = sp.solve(eq, I)
                self.pi_PS_current_pos_sol = [sol.evalf() for sol in solutions if sol.is_real and sol.evalf() > 0]
                self.pi_PS_current = 1000 * self.pi_PS_current_pos_sol[0]
            
            info_text = (
                f"Device: Qontroller '{self.app.currentheaterid[self.currentchannel]}'\n"
                f"Firmware: DummyFirmware\n"
                f"Channels: {self.currentchannel}\n"
                f"Current limit: {self.currentsettings['offset']} mA"
            )
        else:
            info_text = "No settings available"
        
        self.info_label = ctk.CTkLabel(self, text=info_text)
        self.info_label.pack(pady=10)
