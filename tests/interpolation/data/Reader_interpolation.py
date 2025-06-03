# -*- coding: utf-8 -*-
"""
Created on Mon Jun  2 15:19:14 2025

@author: 12434
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

import math
def find_P_aim(P_initial, A, B, theta):
    
    ### We shall keep the fitting method, to get a good initial guess of the heating power.
    ### Then we use this module to extract the precise heating power for the splitting ratio we require.
    ### Pls notice that we need the input from the pkl file, with xdatalist_IObar/cross as the heating power,
    ### ydatalist_IObar/cross as the optical power. We shall modify the importfunc module.
    
    # sorted_pairs = sorted(zip(A, B), key=lambda x: x[0])
    # if not sorted_pairs:
    #     raise ValueError("Arrays A and B must not be empty.")
    
    # A_sorted, B_sorted = zip(*sorted_pairs)
    # A_sorted = list(A_sorted)
    # B_sorted = list(B_sorted)
    
    A_sorted = list(A)
    B_sorted = list(B)
    
    max_OP = max(B_sorted)
    if max_OP == 0:
        raise ValueError("All optical powers are zero.")
    
    
    ratio_target = np.cos(theta/2)**2
    
    
    R = [op / max_OP for op in B_sorted]
    
    
    candidates = []
    for j in range(len(R) - 1):
        r_lo, r_hi = R[j], R[j+1]
        if (r_lo <= ratio_target <= r_hi) or (r_hi <= ratio_target <= r_lo):
            
            p_mid = (A_sorted[j] + A_sorted[j+1]) / 2
            distance = abs(p_mid - P_initial)
            candidates.append((distance, j))
    
    if not candidates:
        return P_initial
    
    
    candidates.sort()
    j = candidates[0][1]
    P_lo, P_hi = A_sorted[j], A_sorted[j+1]
    R_lo, R_hi = R[j], R[j+1]
    
    
    delta = R_hi - R_lo
    if delta == 0:
        return (P_lo + P_hi) / 2
    else:
        t = (ratio_target - R_lo) / delta
        return P_lo + t * (P_hi - P_lo)  ### Find the final target power






# === Readout of the sweep file ===
#file_path1 = "H1_theta_200stps.csv"
#file_path1 = 'G1_theta_200_steps.csv'
# file_path1 = 'F1_theta_200_steps.csv'
# file_path1 = 'E1_theta_200_steps.csv'
# file_path1 = 'E2_theta_200_steps.csv'
file_path1 = 'G2_theta_200_steps.csv'

current_dir = os.path.dirname(__file__)
file_path1 = os.path.join(current_dir, file_path1)
df = pd.read_csv(file_path1, skiprows=1, header=None)

if df.iloc[0,2] > df.iloc[0, 3]:
    x1 = 2
    x2 = 3
else:
    x1 = 3
    x2 = 2
y1 = df.iloc[:, x1]
y2 = df.iloc[:, x2]

theta = np.linspace(0, 2*np.pi, 200)

y1_sim = np.cos(theta/2)**2
y1_norm = y1/(np.abs(y1)+np.abs(y2))

### A testing angle
theta1 = find_P_aim(0.5*np.pi, theta, y1_norm, 0.5*np.pi)


#### An look-up file
theta_corrected = []
y_test = []
for i in range(len(theta)):
    theta_corrected.append( find_P_aim(theta[i], theta, y1_norm, theta[i]) )
    y_test.append(np.cos(find_P_aim(theta[i], theta, y1_norm, theta[i])/2)**2)
    
    




def theta_trans(the, theta, theta_corrected):
    x = the % (2*np.pi)
    print(x)
    #searchsorted
    i_lo = np.searchsorted(theta, x, side='right')-1  # Find the first >= x position
    i_hi = i_lo + 1   # Find the last <= x position
    print(i_hi, i_lo)
    
    th_l = theta[i_lo]
    th_h = theta[i_hi]
    th_l2 = theta_corrected[i_lo]
    print(th_l2)
    th_h2 = theta_corrected[i_hi]
    
    if abs(th_h2 - th_l2) <= 0.5:
        y = (x - th_l)*(th_h2 - th_l2)/(th_h - th_l) + th_l2
        print('Yes interpolation!')
    else:
        y = th_l2
        print('No interpolation, just initial angle')
    return y
        
    
   

th_test =  1.65
th_test*= np.pi

a1 = theta_trans(th_test, theta, theta_corrected)  
print('Initial:', th_test/np.pi, "\u03C0"," "*4, 'Corrected:', f"{a1/np.pi:.5g}", "\u03C0")  

def picplot():
    plt.close('all')
    # 1. 创建图形并设置大小
    plt.figure(figsize=(12, 6)) # figsize 应用于 plt.figure()

    # --- 第一个子图 ---
    plt.subplot(211)
    plt.plot(theta, y1_sim, label='Theoretical')
    plt.scatter(theta, y1_norm, label='Tested')
    plt.xlabel('Angles', fontsize=18)
    plt.ylabel('Ratio', fontsize=18)
    plt.title('First Subplot: Theoretical vs Tested Ratio', fontsize=20) # 添加标题
    plt.legend(fontsize=14)
    plt.grid(True) # 添加网格线，可选

    # # --- 第二个子图 ---
    # plt.subplot(212)
    # plt.scatter(theta, y_test, label='Corrected', color='green') # 使用不同颜色区分
    # plt.plot(theta, y1_sim, label='Theoretical', linestyle='--') # 使用不同线型区分
    # # 为第二个子图添加 xlabel 和 ylabel
    # plt.xlabel('Angles', fontsize=18) # 假设 x 轴仍然是 Angles
    # plt.ylabel('Value', fontsize=18) #  Y轴标签，根据 y_test 和 y1_sim 的含义确定，这里用 'Value' 作为示例
    # plt.title('Second Subplot: Corrected vs Theoretical Value', fontsize=20) # 添加标题
    # plt.legend(fontsize=14)
    # plt.grid(True) # 添加网格线，可选

    # 自动调整子图参数，以给定的填充方式填充整个图像区域，防止标签重叠

    plt.subplot(212)
    th_plt = th_test % (2*np.pi)
    plt.scatter(theta, theta_corrected, color = 'g')
    plt.scatter(th_plt, a1, marker = 's', color = 'r', s = 50, alpha = 0.98)
    plt.xlabel('Angles we desire', fontsize = 18)
    plt.ylabel('Angles we type in', fontsize = 18)
    plt.grid(True)
    plt.tight_layout()

    plt.show()



