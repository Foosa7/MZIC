# -*- coding: utf-8 -*-
"""
Created on Thu Apr  3 17:10:09 2025

@author: 12434
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

plt.close('all')
# 读取CSV文件，跳过第一行表头
file_path1 = r"C:\Users\hp-ma\Downloads\Full-sweep\g1-sweeep.csv"
#file_path1 = "C4_part4.csv"
#file_path2= "C4_100stps_0425_3a.csv"

# 读取数据（跳过第一行表头）
df = pd.read_csv(file_path1, skiprows=1, header=None)


# 提取所需列
# G1 = 0.07
# H1 = 0.04
x = df.iloc[:, 1]  # 第一列作为横坐标
stp = 200  # 步数
shift = 0.07
theta = np.linspace(0, 2*np.pi, stp)

theta_shift = []
for i in range(len(theta)):
    theta_shift.append(theta[i])
for i in range(len(theta_shift)):
    if i<10:
        theta_shift[i] += -0.05*np.pi
    if 10<=i <=30:
        theta_shift[i] += -0.12*np.pi
    if  30<i<= 60:
        theta_shift[i] += -0.13*np.pi
    if  70>i>60:
        theta_shift[i] +=-0.12*np.pi
    if  80>i>=70:
        theta_shift[i] +=-0.10*np.pi
    if  85>i>=80:
        theta_shift[i] +=-0.08*np.pi
    if  i>=85:
        theta_shift[i] +=-0.055*np.pi
y1 = df.iloc[:, 2]
y2 = df.iloc[:, 3]
R_exp = y1/(y1+y2)
R_sim = np.sin(theta/2)**2
# R_sim = np.cos(theta/2)**2

plt.figure( figsize = (10, 6))
plt.plot(theta, R_sim, label = 'Sim', color = 'b')
plt.scatter(theta_shift, R_exp, color = 'g', label = 'Exp')
plt.legend(fontsize = 24)
plt.title(f'G1_theta Shift {shift} \u03C0', fontsize = 28)
plt.show()