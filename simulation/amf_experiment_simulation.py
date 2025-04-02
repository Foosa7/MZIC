#!/usr/bin/env python3
import numpy as np
from scipy.linalg import expm
import matplotlib.pyplot as plt

def build_unitary_at_timestep(current_time, H1, H2, H3, T_period, direction):
    """
    Builds the 3×3 time-evolving unitary U(t) at 'current_time', 
    using the sequence H1 -> H2 -> H3 (for CW) or reversed (for CCW).
    
    - T_period is split into three segments of length T_period/3.
    - If current_time spans multiple full periods, we apply [U_cycle]^q 
      where U_cycle = exp(-i * H3 * seg) exp(-i * H2 * seg) exp(-i * H1 * seg).
    - Then we apply the leftover partial remainder r in a piecewise manner 
      (first under H1, then H2, then H3, or reversed if direction='CCW').
    """

    T_seg = T_period / 3.0

    def mod_with_quotient(x, modval):
        quotient = int(x // modval)  # number of full cycles
        remainder = x % modval
        return quotient, remainder
    
    # Figure out how many full cycles fit into current_time:
    q, r = mod_with_quotient(current_time, T_period)
    
    # The Hamiltonian sequence depends on direction
    if direction == "CW":
        H_seq = [H1, H2, H3]
    else:  # direction == "CCW"
        H_seq = [H3, H2, H1]
    
    # One full cycle's unitary:
    U_cycle = expm(-1j * T_seg * H_seq[2]) @ expm(-1j * T_seg * H_seq[1]) @ expm(-1j * T_seg * H_seq[0])
    
    # Apply q full cycles:
    # matrix_power is for integer exponent; it does U_cycle^q
    U_full = np.linalg.matrix_power(U_cycle, q)
    
    # Apply leftover remainder r, in three segments (or until r is exhausted)
    rem_U = np.eye(3, dtype=complex)
    for H in H_seq:
        if r >= T_seg:
            # If remainder covers a full segment, apply that
            rem_U = expm(-1j * T_seg * H) @ rem_U
            r -= T_seg
        elif r > 1e-14:
            # If there's a partial leftover, apply that and we are done
            rem_U = expm(-1j * r * H) @ rem_U
            r = 0
            break
        else:
            break
    
    # The final 3×3 time-evolution operator:
    U_total = rem_U @ U_full
    
    return U_total

def main():
    # --- Parameters ---
    c_val = 1.0            # coupling constant
    rabi_cycles = 3.0      # how many "Rabi cycles" in each T_period
    T_period = rabi_cycles * (np.pi / (2.0 * c_val))
    
    T_total = 3 * T_period  # For example, simulate 3 periods total
    print(T_total)
    N_val   = 300           # number of time steps
    direction = "CW"        # can set "CW" or "CCW"
    
    # --- Define the 3 Hamiltonians ---
    H1 = np.array([[0,     c_val, 0    ],
                   [c_val, 0,     0    ],
                   [0,     0,     1    ]], dtype=float)

    H2 = np.array([[1,     0,     0    ],
                   [0,     0,     c_val],
                   [0,     c_val, 0    ]], dtype=float)

    H3 = np.array([[0,     0,     c_val],
                   [0,     1,     0    ],
                   [c_val, 0,     0    ]], dtype=float)

    # --- Initial state: site 1 excited (normalized) ---
    #   a = [1, 0, 0]^T
    a_init = np.array([1.0, 0.0, 0.0], dtype=complex)
    
    # --- Time array ---
    time_array = np.linspace(0, T_total, N_val)
    
    # For storing population on each site over time:
    pop_data = np.zeros((N_val, 3), dtype=float)
    
    # --- Compute the state at each time step ---
    for i, t in enumerate(time_array):
        # Build the piecewise unitary for time t
        U_t = build_unitary_at_timestep(
            current_time = t,
            H1=H1, H2=H2, H3=H3,
            T_period = T_period,
            direction = direction
        )
        # Apply to the initial state
        psi_t = U_t @ a_init
        # Normalize if needed (should already be unitary, but we can be safe)
        # psi_t = psi_t / np.linalg.norm(psi_t)
        
        # Compute site populations = |psi_t|^2
        pop_data[i, :] = np.abs(psi_t)**2
    
    # --- Plot the population vs time ---
    plt.figure(figsize=(8,6))
    plt.plot(time_array, pop_data[:,0], label='Site 1')
    plt.plot(time_array, pop_data[:,1], label='Site 2')
    plt.plot(time_array, pop_data[:,2], label='Site 3')
    
    plt.xlabel("Time")
    plt.ylabel("Population")
    plt.title(f"3-Site Evolution ({direction} direction)\n" 
              f"c={c_val}, T_period={T_period:.3f}")
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
