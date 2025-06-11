# app/utils/interpolation/Reader_interpolation.py
"""
Interpolation module for phase correction.
Handles sweep file loading and angle transformation calculations.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
import os
from typing import Tuple, List, Optional, Dict

class InterpolationManager:
    """Manages interpolation operations for phase correction"""
    
    def __init__(self):
        self.theta: Optional[np.ndarray] = None
        self.y1_norm: Optional[np.ndarray] = None
        self.theta_corrected: Optional[List[float]] = None
        self.y_test: Optional[List[float]] = None
        self.current_file: Optional[str] = None
        
        # Update base_dir to point to the csv data folder
        self.base_dir = os.path.join(os.path.dirname(__file__), "data")
        
        # Available sweep files
        self.available_files = [
            "H1_theta_200_steps.csv",
            "G1_theta_200_steps.csv",
            "G2_theta_200_steps.csv",
            "F1_theta_200_steps.csv",
            "E1_theta_200_steps.csv",
            "E2_theta_200_steps.csv"
        ]

    def get_available_files(self) -> List[str]:
        """
        Get list of available sweep files.
        
        Returns:
            List of available sweep file names
        """
        return self.available_files.copy()

    def load_sweep_file(self, filename: str) -> None:
        """
        Load sweep file and prepare interpolation variables.
        
        Args:
            filename: Name of the CSV file to load
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is invalid
        """
        self.current_file = filename
        path = os.path.join(self.base_dir, filename)
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Sweep file not found: {path}")
        
        try:
            df = pd.read_csv(path, skiprows=1, header=None)
            
            # 计算倒数第二列和最后一列的索引
            col_y2 = df.shape[1] - 2
            col_y1 = df.shape[1] - 1

            # 比较第0行这两列的值
            if df.iloc[0, col_y2] > df.iloc[0, col_y1]:
                x1 = col_y2
                x2 = col_y1
            else:
                x1 = col_y1
                x2 = col_y2

            y1 = df.iloc[:, x1]
            y2 = df.iloc[:, x2]
            
            # Generate theta array
            self.theta = np.linspace(0, 2*np.pi, 200)
            
            #y1_sim = np.cos(self.theta/2)**2
            self.y1_norm = np.abs(y1)/(np.abs(y1)+np.abs(y2))
            
            # Generate corrected theta values
            self._generate_theta_corrected()
            
        except Exception as e:
            raise ValueError(f"Failed to load sweep file: {str(e)}")
    
    def _generate_theta_corrected(self) -> None:
        """Generate the corrected theta values and test values"""
        if self.theta is None or self.y1_norm is None:
            raise ValueError("Data not loaded")
            
        self.theta_corrected = []
        self.y_test = []
        
        for i in range(len(self.theta)):
            corrected = self.find_P_aim(self.theta[i], self.theta, self.y1_norm, self.theta[i])
            self.theta_corrected.append(corrected)
            self.y_test.append(np.cos(corrected/2)**2)
    
    def find_P_aim(self, P_initial: float, A: np.ndarray, B: np.ndarray, theta: float) -> float:
        """
        Find target power for desired splitting ratio.
        
        Args:
            P_initial: Initial power estimate
            A: Array of angle values
            B: Array of normalized optical power values
            theta: Target angle in radians
            
        Returns:
            Target power value
        """
        A_sorted = list(A)
        B_sorted = list(B)
        
        max_OP = max(B_sorted)
        if max_OP == 0:
            raise ValueError("All optical powers are zero.")
        
        ratio_target = np.cos(theta/2)**2
        R = [op / max_OP for op in B_sorted]
        
        # Find candidate intervals
        candidates = []
        for j in range(len(R) - 1):
            r_lo, r_hi = R[j], R[j+1]
            if (r_lo <= ratio_target <= r_hi) or (r_hi <= ratio_target <= r_lo):
                p_mid = (A_sorted[j] + A_sorted[j+1]) / 2
                distance = abs(p_mid - P_initial)
                candidates.append((distance, j))
        
        if not candidates:
            return P_initial
        
        # Select the closest candidate
        candidates.sort()
        j = candidates[0][1]
        P_lo, P_hi = A_sorted[j], A_sorted[j+1]
        R_lo, R_hi = R[j], R[j+1]
        
        # Linear interpolation
        delta = R_hi - R_lo
        if delta == 0:
            return (P_lo + P_hi) / 2
        else:
            t = (ratio_target - R_lo) / delta
            return P_lo + t * (P_hi - P_lo)
    
    def theta_trans(self, the: float) -> Tuple[float, bool]:
        """
        Transform theta value using interpolation.
        
        Args:
            the: Input angle in radians
            
        Returns:
            Tuple of (corrected angle, whether interpolation was used)
            
        Raises:
            ValueError: If no sweep file is loaded
        """
        if self.theta is None or self.theta_corrected is None:
            raise ValueError("No sweep file loaded. Call load_sweep_file() first.")
        
        x = the % (2*np.pi)
        
        # Find the interpolation interval
        i_lo = np.searchsorted(self.theta, x, side='right') - 1
        i_hi = min(i_lo + 1, len(self.theta) - 1)
        
        th_l = self.theta[i_lo]
        th_h = self.theta[i_hi]
        th_l2 = self.theta_corrected[i_lo]
        th_h2 = self.theta_corrected[i_hi]
        
        # Check if interpolation is valid
        if abs(th_h2 - th_l2) <= 0.5:
            y = (x - th_l) * (th_h2 - th_l2) / (th_h - th_l) + th_l2
            interpolated = True
        else:
            y = th_l2
            interpolated = False
            
        return y, interpolated
    
    def create_plot(self, angle_input_rad: float) -> plt.Figure:
        """
        Create interpolation plots without showing them.
        
        Args:
            angle_input_rad: Input angle in radians (not multiplied by pi)
            
        Returns:
            Matplotlib figure object
        """
        if self.theta is None:
            raise ValueError("No sweep file loaded.")
        
        th_test = angle_input_rad * np.pi
        a1, interpolated = self.theta_trans(th_test)
        
        # Create figure with dark theme support
        fig = plt.figure(figsize=(10, 6))
        fig.patch.set_facecolor('white')
        
        # First subplot: Theoretical vs Tested Ratio
        ax1 = plt.subplot(211)
        y1_sim = np.cos(self.theta/2)**2
        ax1.plot(self.theta, y1_sim, 'b-', label='Theoretical', linewidth=2)
        ax1.scatter(self.theta, self.y1_norm, c='orange', label='Tested', s=20, alpha=0.7)
        ax1.set_xlabel('Angles (rad)', fontsize=14)
        ax1.set_ylabel('Ratio', fontsize=14)
        ax1.set_title(f'Theoretical vs Tested Ratio ({self.current_file})', fontsize=16)
        ax1.legend(fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim([0, 2*np.pi])
        
        # Add pi markers on x-axis
        pi_ticks = np.array([0, np.pi/2, np.pi, 3*np.pi/2, 2*np.pi])
        pi_labels = ['0', 'π/2', 'π', '3π/2', '2π']
        ax1.set_xticks(pi_ticks)
        ax1.set_xticklabels(pi_labels)
        
        # Second subplot: Angle Transformation
        ax2 = plt.subplot(212)
        th_plt = th_test % (2*np.pi)
        ax2.scatter(self.theta, self.theta_corrected, c='green', s=20, alpha=0.7, label='Transformation')
        ax2.scatter(th_plt, a1, marker='s', color='red', s=100, alpha=0.98, 
                   label=f'Input: {angle_input_rad:.3f}π → Output: {a1/np.pi:.3f}π')
        
        # Add diagonal reference line
        #ax2.plot([0, 2*np.pi], [0, 2*np.pi], 'k--', alpha=0.3, label='Identity')
        
        ax2.set_xlabel('Desired Angles (rad)', fontsize=14)
        ax2.set_ylabel('Corrected Angles (rad)', fontsize=14)
        ax2.set_title('Angle Transformation', fontsize=16)
        ax2.legend(fontsize=10)
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim([0, 2*np.pi])
        ax2.set_ylim([0, 2*np.pi])
        
        # Add pi markers
        ax2.set_xticks(pi_ticks)
        ax2.set_xticklabels(pi_labels)
        ax2.set_yticks(pi_ticks)
        ax2.set_yticklabels(pi_labels)
        
        # Add interpolation status
        #status_text = "Interpolation: " + ("Yes" if interpolated else "No")
        # ax2.text(0.02, 0.98, status_text, transform=ax2.transAxes, 
        #         verticalalignment='top', fontsize=10,
        #         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        return fig
    
    def get_corrected_angle(self, angle_rad: float) -> Dict[str, float]:
        """
        Get corrected angle with additional information.
        
        Args:
            angle_rad: Input angle in radians
            
        Returns:
            Dictionary with input, output, and whether interpolation was used
        """
        if self.theta is None:
            raise ValueError("No sweep file loaded.")
            
        corrected, interpolated = self.theta_trans(angle_rad)
        
        return {
            'input_rad': angle_rad,
            'input_pi': angle_rad / np.pi,
            'output_rad': corrected,
            'output_pi': corrected / np.pi,
            'interpolated': interpolated,
            'file': self.current_file
        }

# Create a singleton instance for global access
interpolation_manager = InterpolationManager()

# For backward compatibility, expose the old functions
def load_sweep_file(filename: str) -> None:
    """Backward compatible function"""
    interpolation_manager.load_sweep_file(filename)

def picplot(angle_input_rad: float) -> None:
    """Backward compatible function"""
    fig = interpolation_manager.create_plot(angle_input_rad)
    plt.show()

def theta_trans(the: float, theta: np.ndarray, theta_corrected: List[float]) -> float:
    """Backward compatible function (not recommended for new code)"""
    # This is kept for compatibility but should not be used
    interpolation_manager.theta = theta
    interpolation_manager.theta_corrected = theta_corrected
    result, _ = interpolation_manager.theta_trans(the)
    return result