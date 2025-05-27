# app/utils/mzi_convention.py
import numpy as np
from app.imports import *

def clements_to_chip(clements_bs_list):

    for bs in clements_bs_list:
        bs.theta = 2 * bs.theta 
        
        if abs(bs.theta) < 1e-10:
            bs.theta = 0
        bs.theta = format(bs.theta/np.pi,'.10f')
     
        if abs(bs.phi) < 1e-10:
            bs.phi = 0
        bs.phi = format(bs.phi/np.pi,'.10f')
    

