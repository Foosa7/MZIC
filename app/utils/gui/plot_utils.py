import matplotlib.pyplot as plt
import numpy as np
from app.utils.appdata import AppData  # <-- Add this import
import logging


class PlotUtils:
    @staticmethod
    def create_resistance_plot(params, cross_label, channel_symbol, target_channel):
        """Generate styled resistance characterization plot"""
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#363636')
        
        ax.plot(params['currents'], params['voltages'], 
            'o', color='white', label='Measured')
        x_fit = np.linspace(min(params['currents']), max(params['currents']), 100)
        y_fit = params['a']*x_fit**3 + params['c']*x_fit + params['d']
        ax.plot(x_fit, y_fit, color='#ff4b4b', linewidth=1, label='Cubic Fit')

        selected = list(AppData.selected_labels)
        cross_label = selected[-1] if selected else ""  # Use the latest selected label

        title_str = f"Resistance Characterization of {cross_label}:{channel_symbol} at Channel {target_channel}"

        ax.set_title(title_str, color='white', fontsize=12)
        ax.set_xlabel("Current (mA)", color='white', fontsize=10)
        ax.set_ylabel("Voltage (V)", color='white', fontsize=10)
        
        ax.tick_params(colors='white', which='both')
        for spine in ax.spines.values():
            spine.set_color('white')
            
        legend = ax.legend(frameon=True, facecolor='#2b2b2b', edgecolor='white')
        for text in legend.get_texts():
            text.set_color('white')

        fig.tight_layout()        
        return fig

    @staticmethod
    def create_phase_plot(params, cross_label, channel_symbol, target_channel, io_config):
        """Generate phase calibration plot based on heating power"""
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#363636')

        # Plot measured data
        ax.plot(params['heating_powers'], params['optical_powers'],
                'o', color='white', label='Measured')

        # Fit curve
        x_fit = np.linspace(min(params['heating_powers']), max(params['heating_powers']), 200)

        if io_config == "cross":
            y_fit = params['amp'] * np.cos(params['omega'] * x_fit + params['phase']) + params['offset']
        else:
            y_fit = -params['amp'] * np.cos(params['omega'] * x_fit + params['phase']) + params['offset']

        ax.plot(x_fit, y_fit, color='#ff4b4b', linewidth=1, label='Cosine Fit')

        selected = list(AppData.selected_labels)
        cross_label = selected[-1] if selected else ""

        title_str = f"Phase Characterization of {cross_label}:{channel_symbol} at Channel {target_channel} ({io_config.capitalize()})"
        ax.set_title(title_str, color='white', fontsize=12)
        ax.set_xlabel("Heating Power (mW)", color='white', fontsize=10)
        ax.set_ylabel("Optical Power (mW)", color='white', fontsize=10)

        ax.tick_params(colors='white', which='both')
        for spine in ax.spines.values():
            spine.set_color('white')

        legend = ax.legend(loc='upper left', frameon=True, facecolor='#2b2b2b', edgecolor='white')
        for text in legend.get_texts():
            text.set_color('white')

        return fig

    def plot_resistance(self, currents, voltages, resistances, target_channel, current=None, channel_type=None, phase_selector=None):
        """Generate styled resistance characterization plot using latest selected label"""
        try:
            # Always use the latest selected label
            selected = list(AppData.selected_labels)
            cross_label = selected[-1] if selected else ""
            channel_symbol = "θ" if channel_type == "theta" else "φ"

            # Create plot with dark theme
            fig, ax = plt.subplots(figsize=(6, 4))
            fig.patch.set_facecolor('#2b2b2b')
            ax.set_facecolor('#363636')
            
            # Plot data points and fit curve
            ax.plot(currents, voltages, 'o', color='white', label='Measured')
            
            # Calculate fit curve
            x_fit = np.linspace(min(currents), max(currents), 100)
            y_fit = resistances[0] * x_fit**3 + resistances[1] * x_fit + resistances[2]
            ax.plot(x_fit, y_fit, color='#ff4b4b', linewidth=1, label='Cubic Fit')

            # Set title with channel info
            if cross_label and channel_symbol:
                title_str = f"Resistance Characterization of {cross_label}:{channel_symbol} at Channel {target_channel}"
            else:
                title_str = f"Resistance Characterization of Channel {target_channel}"
                
            ax.set_title(title_str, color='white', fontsize=12)
            ax.set_xlabel("Current (mA)", color='white', fontsize=10)
            ax.set_ylabel("Voltage (V)", color='white', fontsize=10)
            
            # Configure ticks and borders
            ax.tick_params(colors='white', which='both')
            for spine in ax.spines.values():
                spine.set_color('white')
                
            # Legend styling
            legend = ax.legend(loc='upper left', frameon=True, facecolor='#2b2b2b', edgecolor='white')
            for text in legend.get_texts():
                text.set_color('white')

            fig.tight_layout()        
            return fig
            
        except Exception as e:
            logging.error(f"Creating resistance plot: {str(e)}")
            return None

    def plot_phase(self, heating_powers, optical_powers, fitfunc, popt, target_channel, io_config, current=None, channel_type=None):
        """Generate phase calibration plot using heating power instead of current"""
        try:
            selected = list(AppData.selected_labels)
            cross_label = selected[-1] if selected else ""
            channel_symbol = "θ" if channel_type == "theta" else "φ"

            fig, ax = plt.subplots(figsize=(6, 4))
            fig.patch.set_facecolor('#2b2b2b')
            ax.set_facecolor('#363636')

            # Measured data
            ax.plot(heating_powers, optical_powers, 'o', color='white', label='Measured')

            # Fit curve
            x_fit = np.linspace(min(heating_powers), max(heating_powers), 200)
            y_fit = fitfunc(x_fit, *popt)
            ax.plot(x_fit, y_fit, color='#ff4b4b', linewidth=1, label='Cosine Fit')

            # Title and labels
            if cross_label and channel_symbol:
                title_str = f"Phase Characterization of {cross_label}:{channel_symbol} at Channel {target_channel} ({io_config.capitalize()})"
            else:
                title_str = f"Phase Characterization of Channel {target_channel} ({io_config.capitalize()})"

            ax.set_title(title_str, color='white', fontsize=12)
            ax.set_xlabel("Heating Power (mW)", color='white', fontsize=10)
            ax.set_ylabel("Optical Power (mW)", color='white', fontsize=10)

            ax.tick_params(colors='white', which='both')
            for spine in ax.spines.values():
                spine.set_color('white')

            legend = ax.legend(loc='upper left', frameon=True, facecolor='#2b2b2b', edgecolor='white')
            for text in legend.get_texts():
                text.set_color('white')

            fig.tight_layout()
            return fig

        except Exception as e:
            logging.error(f"Creating phase plot: {str(e)}")
            return None
