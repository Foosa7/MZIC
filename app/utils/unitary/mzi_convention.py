# app/utils/mzi_convention.py
import numpy as np
from app.imports import *

def clements_to_chip(clements_bs_list):
    '''
    Converts the beam splitters angles from Clements convention to the chip convention.
    Returns a new list of beam splitters with converted angles.
    
    Clements MZI convention:

            e^{iphi_clements}*cos(theta_clements)     -sin(theta_clements)
            e^{iphi_clements}*sin(theta_clements)     cos(theta_clements)
            
    -----------------------
    Chip MZI convention:

            e^{iphi_chip}*sin(theta_chip/2)     cos(theta_chip/2)
            e^{iphi_chip}*cos(theta_chip/2)     -sin(theta_chip/2)
            
    => phi_chip = phi_clements + pi,  theta_chip = -2*theta_clements - pi, or theta_chip = 2*theta_clements + pi (factoring out minus sign)
    '''

    for bs in clements_bs_list:
        #bs.theta = 2*bs.theta
        bs.theta = 2 * bs.theta + np.pi
        #bs.theta = -2 * bs.theta - np.pi

        bs.theta = bs.theta % (2*np.pi)
        if abs(bs.theta) < 1e-10:
            bs.theta = 0
        bs.theta = format(bs.theta/np.pi,'.10f')
     
        bs.phi = bs.phi + np.pi
        #bs.phi = bs.phi 
        bs.phi = bs.phi % (2*np.pi)
        if abs(bs.phi) < 1e-10:
            bs.phi = 0
        bs.phi = format(bs.phi/np.pi,'.10f')
    

