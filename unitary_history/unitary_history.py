import os
import numpy as np
import matplotlib.pyplot as plt

def main():
    """
    Example script:
    - Assume your folder of saved unitaries is in './unitary_history'
    - Each file is named 'unitary_step_XXX.npy' (XXX = 3-digit index)
    - We'll load each 8x8 matrix in ascending order:
        unitary_step_001.npy, unitary_step_002.npy, ..., unitary_step_300.npy
    - Then we apply each matrix to an 8-element input vector [1, 0, 0, 0, 0, 0, 0, 0].
    - We'll record the outputs in channels 1, 2, and 3 (which are array indices [0], [1], [2]).
    """

    n_channels = 8
    max_steps = 300  # or however many steps you saved

    # Define the input: "light in channel 1" => vector = [1,0,0,0,0,0,0,0]
    input_vec = np.zeros(n_channels, dtype=complex)
    input_vec[0] = 1.0

    # Prepare lists (or arrays) to store output intensities
    # We want output1, output2, output3 => indices [0], [1], [2]
    out1 = []
    out2 = []
    out3 = []

    # Loop over all saved unitary files
    for step in range(1, max_steps+1):
        # Construct the file path: e.g. "unitary_step_001.npy"
        filename = f"unitary_step_{step:03d}.npy"
       

        # Load the 8x8 unitary
        U = np.load(filename)

        # Multiply U by the input vector
        output_vec = U @ input_vec  # shape (8,)

        # Compute intensities (magnitude^2)
        p1 = np.abs(output_vec[0])**2
        p2 = np.abs(output_vec[1])**2
        p3 = np.abs(output_vec[2])**2

        out1.append(p1)
        out2.append(p2)
        out3.append(p3)

    # Convert to arrays for easier plotting
    out1 = np.array(out1)
    out2 = np.array(out2)
    out3 = np.array(out3)

    # Create a step-index array (for x-axis)
    steps_array = np.arange(1, len(out1)+1)

    # Plot
    plt.figure(figsize=(8,6))
    plt.plot(steps_array, out1, label="Output 1")
    plt.plot(steps_array, out2, label="Output 2")
    plt.plot(steps_array, out3, label="Output 3")
    plt.xlabel("Step index")
    plt.ylabel("Intensity (|amplitude|^2)")
    plt.title("Output intensities for input=channel1 over time steps")
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
