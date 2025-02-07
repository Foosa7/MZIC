# app/utils/utils.py

import math
import numpy as np
import sympy as sp
from tkinter import messagebox

def apply_phase(custom_grid, qontrol, app):
    """
    For each input box in custom_grid.input_boxes, read the entered phase (phi),
    validate it using app.allowedinputvalues, compute the required current, update the Qontrol device
    via its set_current method, and store the derived current in app.derived_current_list.
    """
    for cross_label, boxes in custom_grid.input_boxes.items():
        phi_str = boxes['phi_entry'].get().strip()
        
        if phi_str == "":
            messagebox.showerror("Error", f"Phase entry is empty for channel {cross_label}.")
            continue

        illegal = False
        dot_count = 0
        for ch in phi_str:
            if ch not in app.allowedinputvalues:
                illegal = True
                break
            if ch == '.':
                dot_count += 1
                if dot_count > 1:
                    illegal = True
                    break
        if illegal:
            messagebox.showerror("Error", f"Invalid phase entry for channel {cross_label}.\nEnter a numeric value.")
            boxes['phi_entry'].delete(0, 'end')
            continue

        try:
            phi_val = float(phi_str)
        except Exception as e:
            messagebox.showerror("Error", f"Conversion error for channel {cross_label}: {e}")
            boxes['phi_entry'].delete(0, 'end')
            continue

        if phi_val < app.phase_offset:
            messagebox.showerror("Error", f"Entered phase ({phi_val}) for channel {cross_label} is less than the offset phase ({app.phase_offset}).")
            boxes['phi_entry'].delete(0, 'end')
            continue

        if not hasattr(app, "phi_phase_list"):
            app.phi_phase_list = {}
        app.phi_phase_list[cross_label] = phi_val

        # Compute the current based on the chosen fit function.
        if app.current_fit == app.fit_func[0]:
            P = abs((phi_val * math.pi - app.phase_offset) / app.b)
            current = float(round(1000 * math.sqrt(P / (app.R * 1000)), 2))
        elif app.current_fit == app.fit_func[1]:
            P = abs((phi_val * math.pi - app.phase_offset) / app.b)
            P = P / 1000
            I = sp.symbols('I', positive=True, real=True)
            eq = sp.Eq(P / app.R0, I**2 + app.alpha * I**4)
            sol = sp.solve(eq, I)
            sol_positive = [float(s.evalf()) for s in sol if s.is_real and s.evalf() > 0]
            if not sol_positive:
                messagebox.showerror("Error", f"No valid current solution for channel {cross_label}.")
                boxes['phi_entry'].delete(0, 'end')
                continue
            current = float(round(1000 * sol_positive[0], 5))
        else:
            messagebox.showerror("Error", "Unknown current fit function.")
            continue

        if not hasattr(app, "derived_current_list"):
            app.derived_current_list = {}
        app.derived_current_list[cross_label] = current

        try:
            # Extract digits from cross_label and subtract 1 to get a zero-based channel index.
            channel_index = int(''.join(filter(str.isdigit, cross_label))) - 1
        except Exception as e:
            messagebox.showerror("Error", f"Channel mapping error for {cross_label}: {e}")
            boxes['phi_entry'].delete(0, 'end')
            continue

        # Use the Qontrol device directly.
        if qontrol and qontrol.device:
            try:
                qontrol.set_current(channel_index, current)
                print(f"Set current for channel {channel_index} (label {cross_label}) to {current} mA")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to set current for channel {cross_label}: {e}")
        else:
            messagebox.showerror("Error", "No Qontrol device connected.")

        boxes['phi_entry'].delete(0, 'end')
    
    messagebox.showinfo("Apply Phase", "Phase values applied and currents updated for selected channels.")
