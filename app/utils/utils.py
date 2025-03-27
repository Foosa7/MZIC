# app/utils/utils.py

import math
import numpy as np
import sympy as sp
from tkinter import messagebox
import os
import pickle
from io import BytesIO
from tkinter import filedialog, messagebox

def load_config(config_path="config/settings.json"):
    """Load the configuration file."""
    if os.path.exists(config_path):
        with open(config_path, "r") as file:
            return json.load(file)
    return {}

def import_pickle(config):
    """Loads a pickle file from the path in config and returns the data."""
    import_file = config.get("default_config", "")

    # Ensure the file path is correctly formatted for Windows
    import_file = os.path.normpath(import_file)

    if not import_file or not os.path.exists(import_file):
        print(f"Default pickle file not found: {import_file}")
        return None

    with open(import_file, "rb") as file:
        imported_data = pickle.load(file)

    print(f"Successfully imported {import_file}")
    return imported_data  # Return the loaded data



def importfunc(obj):
    """
    Opens a file dialog to select a pickle file, then imports data from it
    and updates the attributes of the given object 'obj'.
    
    Expected keys in the imported dictionary:
      - 'caliparamlist_lin_cross'
      - 'caliparamlist_lin_bar'
      - 'caliparamlist_lincub_cross'
      - 'caliparamlist_lincub_bar'
      - 'standard_matrices'
      - 'image_map'
      
    The function also reassigns the 'fitfunc' in the matrices if its value is 'fit_cos_func'
    by setting it to obj.fit_cos.
    """
    
    # Ask for the import file.
    import_file = filedialog.askopenfilename(
        title="Open Import File",
        filetypes=[("Pickle Files", "*.pkl")]
    )
    if not import_file:
        messagebox.showinfo("Import Canceled", "No file selected for import.")
        return

    # Load the imported data from the pickle file.
    with open(import_file, "rb") as file:
        imported = pickle.load(file)

    # Reassign the fitfunc back from the reference string.
    for key in ['caliparamlist_lin_cross', 'caliparamlist_lin_bar',
                'caliparamlist_lincub_cross', 'caliparamlist_lincub_bar']:
        if hasattr(obj, key):
            matrix = getattr(obj, key)
            for i, data in enumerate(matrix):
                if isinstance(data, dict) and 'fitfunc' in data:
                    if data['fitfunc'] == 'fit_cos_func':
                        data['fitfunc'] = obj.fit_cos  # Replace with the actual function reference.
                    matrix[i] = data  # Replace with the modified data.

    # Import standard matrices.
    standard_matrices = imported.get("standard_matrices", {})
    for attr_name, matrix in standard_matrices.items():
        if hasattr(obj, attr_name):
            setattr(obj, attr_name, matrix)

    # Import BytesIO matrices from images.
    import_dir = os.path.dirname(import_file)
    image_map = imported.get("image_map", {})
    for matrix_name, image_filenames in image_map.items():
        if hasattr(obj, matrix_name):
            matrix = getattr(obj, matrix_name)
            if isinstance(matrix, list):
                for i, filename in enumerate(image_filenames):
                    image_path = os.path.join(import_dir, filename)
                    if os.path.exists(image_path):
                        with open(image_path, "rb") as img_file:
                            buf = BytesIO(img_file.read())
                            buf.seek(0)  # Reset position
                            # Extend the list if necessary.
                            if i >= len(matrix):
                                matrix.extend([None] * (i + 1 - len(matrix)))
                            matrix[i] = buf

    # messagebox.showinfo("Import Complete",
    #                     f"{import_file}")


# def apply_phase(custom_grid, qontrol, app):
#     """
#     For each input box in custom_grid.input_boxes, read the entered phase (phi),
#     validate it using app.allowedinputvalues, compute the required current, update the Qontrol device
#     via its set_current method, and store the derived current in app.derived_current_list.

#     Mapping:
#       - For a cross label like "A1", the numeric part is extracted.
#       - Channel low  = (numeric - 1) * 2
#       - Channel high = channel low + 1
#     """
#     for cross_label, boxes in custom_grid.input_boxes.items():
#         phi_str = boxes['phi_entry'].get().strip()
        
#         if phi_str == "":
#             messagebox.showerror("Error", f"Phase entry is empty for channel {cross_label}.")
#             continue

#         # Validate phi string.
#         illegal = False
#         dot_count = 0
#         for ch in phi_str:
#             if ch not in app.allowedinputvalues:
#                 illegal = True
#                 break
#             if ch == '.':
#                 dot_count += 1
#                 if dot_count > 1:
#                     illegal = True
#                     break
#         if illegal:
#             messagebox.showerror("Error", f"Invalid phase entry for channel {cross_label}.\nEnter a numeric value.")
#             boxes['phi_entry'].delete(0, 'end')
#             continue

#         try:
#             phi_val = float(phi_str)
#         except Exception as e:
#             messagebox.showerror("Error", f"Conversion error for channel {cross_label}: {e}")
#             boxes['phi_entry'].delete(0, 'end')
#             continue

#         if phi_val < app.phase_offset:
#             messagebox.showerror("Error", f"Entered phase ({phi_val}) for channel {cross_label} is less than the offset phase ({app.phase_offset}).")
#             boxes['phi_entry'].delete(0, 'end')
#             continue

#         if not hasattr(app, "phi_phase_list"):
#             app.phi_phase_list = {}
#         app.phi_phase_list[cross_label] = phi_val

#         # Compute the current based on the chosen fit function.
#         if app.current_fit == app.fit_func[0]:
#             P = abs((phi_val * math.pi - app.phase_offset) / app.b)
#             current = float(round(1000 * math.sqrt(P / (app.R * 1000)), 2))
#         elif app.current_fit == app.fit_func[1]:
#             P = abs((phi_val * math.pi - app.phase_offset) / app.b)
#             P = P / 1000
#             I = sp.symbols('I', positive=True, real=True)
#             eq = sp.Eq(P / app.R0, I**2 + app.alpha * I**4)
#             sol = sp.solve(eq, I)
#             sol_positive = [float(s.evalf()) for s in sol if s.is_real and s.evalf() > 0]
#             if not sol_positive:
#                 messagebox.showerror("Error", f"No valid current solution for channel {cross_label}.")
#                 boxes['phi_entry'].delete(0, 'end')
#                 continue
#             current = float(round(1000 * sol_positive[0], 5))
#         else:
#             messagebox.showerror("Error", "Unknown current fit function.")
#             continue

#         if not hasattr(app, "derived_current_list"):
#             app.derived_current_list = {}
#         app.derived_current_list[cross_label] = current

#         # Map cross label to channels using the numeric part.
#         try:
#             # Extract numeric part from cross_label (e.g. "A1" -> 1, "A2" -> 2, etc.)
#             numeric_part = int(''.join(filter(str.isdigit, cross_label)))
#             channel_low  = (numeric_part - 1) * 2
#             channel_high = channel_low + 1
#         except Exception as e:
#             messagebox.showerror("Error", f"Channel mapping error for {cross_label}: {e}")
#             boxes['phi_entry'].delete(0, 'end')
#             continue

#         # Use the Qontrol device directly.
#         if qontrol and qontrol.device:
#             try:
#                 qontrol.set_current(channel_low, current)
#                 qontrol.set_current(channel_high, current)
#                 print(f"Set current for channels {channel_low} and {channel_high} (label {cross_label}) to {current} mA")
#             except Exception as e:
#                 messagebox.showerror("Error", f"Failed to set current for channel {cross_label}: {e}")
#         else:
#             messagebox.showerror("Error", "No Qontrol device connected.")

#         boxes['phi_entry'].delete(0, 'end')
    
#     messagebox.showinfo("Apply Phase", "Phase values applied and currents updated for selected channels.")


# def fit_func(self, x, y):
#     """ Fit the data to a linear or linear + cubic function """
#     if self.fit == self.fit_func[0]:  # Linear fit
#         elif self.fit == self.fit_func[1]: 
            
#             self.lincubchar_voltage[self.channel] = y
#             self.lincubchar_current[self.channel] = x
            
#             # Design matrix excluding the x^2 term
#             X = np.vstack([x**3, x, np.ones_like(x)]).T
            
#             # Solve for coefficients [a, c, d] using least squares
#             coefficients, residuals, rank, s = np.linalg.lstsq(X, y, rcond=None)
            
#             # Extract coefficients
#             a, c, d = coefficients
#             print(a, c, d)
            
#             self.resistancelist[self.channel] = a*(x**2) + c
#             self.rmin_list[self.channel] = np.min(self.resistancelist[self.channel])
#             self.rmax_list[self.channel] = np.max(self.resistancelist[self.channel])
#             self.alpha_list[self.channel] = a/c
#             self.resistance_parameter_list[self.channel] = [a, c, d] #add resistance, this is a float
            
#             print('Acquired resistance for channel ' +str(self.channel) +" is "+ str(self.resistancelist[self.channel]) + ' Ω '+ 'for the current values '+ str(x*1000)+'mA when when fitted using a linear + cubic function')
            
#             # Set white font colors
#             COLOR = 'white'
#             matplotlib.rcParams['text.color'] = COLOR
#             matplotlib.rcParams['axes.labelcolor'] = COLOR
#             matplotlib.rcParams['xtick.color'] = COLOR
#             matplotlib.rcParams['ytick.color'] = COLOR
            
#             # Create figure and axes explicitly
#             fig, ax = plt.subplots(1, figsize=(6, 4))
            
#             plt.scatter(x,y,label='Measured data points', color='white')
#             plt.plot(x, a*(x**3)+c*(x)+d, label = "Linear +cubic fit", color = "red")
#             #plt.text(endcurr/1000 - 5/1000, 0.7, 'y = ' + '{:.2f}'.format(b) + ' + {:.2f}'.format(a) + 'x', size=9)
#             #plt.text(endcurr/1000 - 5/1000, 0.4, 'Resistance near zero current: ' + '{:.2f}'.format(c) + 'Ω', size=9)
            
#             # Apply custom formatter to x-axis
#             ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value * 1000:.0f}"))
            
#             # Add labels, title, and legend
#             ax.set_xlabel("Applied current (mA)")
#             ax.set_ylabel("Measured voltage (V)")
#             ax.set_title("Characterized Resistance for Channel"+str(self.channel)+"("+str(self.currentheaterid[self.channel])+"): Linear+Cubic fit")  # Adjust channel dynamically
#             ax.legend(loc="best", facecolor="#323334", framealpha=1)
            
#             # Customize appearance
#             ax.set_facecolor("#323334")
#             plt.setp(ax.spines.values(), color=COLOR)
#             fig.patch.set_facecolor("#323334")
            
#             # Show the plot
#             #plt.show()
            
#             # Save plot to a BytesIO buffer
#             buf = BytesIO()
#             print(buf)
#             fig.savefig(buf, format="png")
#             buf.seek(0)  # Reset buffer position to the start

#             self.res_lincub_char_images[self.channel] = buf  # Store the buffer in the array
#             plt.close(fig)  # Close the figure to free memory
            
#             self.image_frame1.your_image.configure(light_image=Image.open(self.res_lincub_char_images[self.channel]), size=(self.image_frame1.IMAGE_WIDTH , self.image_frame1.IMAGE_HEIGHT))
            
#             self.resist_min.configure(text=str(np.round(self.rmin_list[self.channel]/1000, 2)))
#             self.resist_max.configure(text=str(np.round(self.rmax_list[self.channel]/1000, 2)))
#             #self.alpha.configure(text=str(np.round(self.alpha_list[self.channel], 2)))
#         ##########################################################################
#         self.image_frame2.your_image.configure(light_image=Image.open(self.opmodimagechoices[self.fit_index][self.IOconfig_index][self.channel]), size=((250)*(395/278),250))
       
#         if self.calframe is not None:
#             self.calframe.destroy()
        
#         self.calframe = MyCalcFrame_main(self.settings_frame, Channel=self.channel, Fit=self.fit, IOconfig=self.IOconfig)
#         self.calframe.grid(column=0, row=0, padx=10, pady=10, sticky="nsew") 
#         #self.label.configure(text=str(round(self.resistancelist[self.channel][0], 0))) #reconfigure label with value for resistance

# def calibrationplotX(self, channel, xdata, ydata): #calibration plot on the calibration tab

#     self.channel = channel
#     self.xdata = xdata #in mW
#     self.ydata = ydata #in mW
    
#     self.fit = self.fit_func_allchannels[self.channel]
#     self.IOconfig = self.IOconfig_allchannels[self.channel]
#     self.fitnames = np.array(["Linear", "Linear+cubic"])
#     self.currentfit_name = self.fitnames[self.fit_func.index(self.fit)]

#     fitxdata = np.linspace(self.xdata[0], self.xdata[-1], 300)
#     print("CalibrationplotX initiated")

#     if self.fit == self.fit_func[0]:
#         if self.IOconfig == self.IOconfig_options[0]:
#             res = self.fit_cos(self.xdata, self.ydata) #save all the parameters here. saved in a dictionary. accessible from app. 
#             self.caliparamlist_lin_cross[self.channel] = res #save the dictionary of calibration parameters for each channel in a list
            
#         elif self.IOconfig == self.IOconfig_options[1]:
#             res = self.fit_cos_negative(self.xdata, self.ydata) #save all the parameters here. saved in a dictionary. accessible from app. 
#             self.caliparamlist_lin_bar[self.channel] = res #save the dictionary of calibration parameters for each channel in a list
            
#     elif self.fit == self.fit_func[1]:
#         if self.IOconfig == self.IOconfig_options[0]:
#             res = self.fit_cos(self.xdata, self.ydata) #save all the parameters here. saved in a dictionary. accessible from app. 
#             self.caliparamlist_lincub_cross[self.channel] = res #save the dictionary of calibration parameters for each channel in a list
            
#         elif self.IOconfig == self.IOconfig_options[1]:
#             res = self.fit_cos_negative(self.xdata, self.ydata) #save all the parameters here. saved in a dictionary. accessible from app. 
#             self.caliparamlist_lincub_bar[self.channel] = res #save the dictionary of calibration parameters for each channel in a list

    
#     print( "Amplitude=%(amp)s, Angular freq.=%(omega)s, phase=%(phase)s, offset=%(offset)s, Max. Cov.=%(maxcov)s" % res)

#     #set white font colors
#     COLOR = 'white'
#     matplotlib.rcParams['text.color'] = COLOR
#     matplotlib.rcParams['axes.labelcolor'] = COLOR
#     matplotlib.rcParams['xtick.color'] = COLOR
#     matplotlib.rcParams['ytick.color'] = COLOR

#     fig, ax = plt.subplots(1, figsize=(8,4))

#     plt.plot(self.xdata, self.ydata, "ok", label="optical power", color='white')
#     plt.plot(fitxdata, res["fitfunc"](fitxdata), "r-", label="fit", linewidth=2)
#     plt.legend(loc="best", facecolor="#323334", framealpha=1)
#     plt.title("Phase calibration curve for channel "+ str(self.channel)+ " ("+ str(self.currentheaterid[self.channel])+ ")\n"+ str(self.currentfit_name)+ " I-V, "+ self.IOconfig+ " config")


#     ax.set_facecolor("#323334")
#     plt.setp(ax.spines.values(), color=COLOR)
#     plt.xlabel("Heating power (P) mW")
#     plt.ylabel("Optical power (Y) mW")
#     fig.patch.set_facecolor("#323334")
    
#     #reset to default colors
#     COLOR = 'black'
#     matplotlib.rcParams['text.color'] = COLOR
#     matplotlib.rcParams['axes.labelcolor'] = COLOR
#     matplotlib.rcParams['xtick.color'] = COLOR
#     matplotlib.rcParams['ytick.color'] = COLOR

#     #plt.show()
    
#     # Save plot to a BytesIO buffer
#     buf = BytesIO()
#     print(buf)
#     fig.savefig(buf, format="png")
#     buf.seek(0)  # Reset buffer position to the start
    
#     if self.fit == self.fit_func[0]:
#         if self.IOconfig == self.IOconfig_options[0]:
#             self.opmod_lin_char_cross_state_images[self.channel] = buf  # Store the buffer in the array
#             plt.close(fig)  # Close the figure to free memory
#             self.image_frame2.your_image.configure(light_image=Image.open(self.opmod_lin_char_cross_state_images[self.channel]), size=(self.image_frame1.IMAGE_WIDTH , self.image_frame1.IMAGE_HEIGHT))
            
#         elif self.IOconfig == self.IOconfig_options[1]:
#             self.opmod_lin_char_bar_state_images[self.channel] = buf  # Store the buffer in the array
#             plt.close(fig)  # Close the figure to free memory
#             self.image_frame2.your_image.configure(light_image=Image.open(self.opmod_lin_char_bar_state_images[self.channel]), size=(self.image_frame1.IMAGE_WIDTH , self.image_frame1.IMAGE_HEIGHT))
            
#     if self.fit==self.fit_func[1]:
#         if self.IOconfig == self.IOconfig_options[0]:
#             self.opmod_lincub_char_cross_state_images[self.channel] = buf  # Store the buffer in the array
#             plt.close(fig)  # Close the figure to free memory
#             self.image_frame2.your_image.configure(light_image=Image.open(self.opmod_lincub_char_cross_state_images[self.channel]), size=(self.image_frame1.IMAGE_WIDTH , self.image_frame1.IMAGE_HEIGHT))
            
#         elif self.IOconfig == self.IOconfig_options[1]:
#             self.opmod_lincub_char_bar_state_images[self.channel] = buf  # Store the buffer in the array
#             plt.close(fig)  # Close the figure to free memory
#             self.image_frame2.your_image.configure(light_image=Image.open(self.opmod_lincub_char_bar_state_images[self.channel]), size=(self.image_frame1.IMAGE_WIDTH , self.image_frame1.IMAGE_HEIGHT))
    
    
