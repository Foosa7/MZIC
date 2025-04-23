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
        # Convert angle from Clements to chip convention
        theta = 2*bs.theta + np.pi         # raw conversion
        phi   = bs.phi + np.pi

        # -----  wrap θ into the canonical range 0 … π  -----
        theta = theta % (2*np.pi)
        if theta > np.pi:          # equivalent θ that lies in 0…π
                theta -= np.pi         # remove the redundant block sign
                phi   += np.pi         # and compensate it on φ
        # ----------------------------------------------------

        # final normalisation
        theta = 0 if abs(theta) < 1e-10 else theta
        phi   =   phi % (2*np.pi)
        phi   = 0 if abs(phi)   < 1e-10 else phi

        # store as multiples of π 
        bs.theta = format(theta/np.pi, '.10f')
        bs.phi   = format(phi  /np.pi, '.10f')
        

