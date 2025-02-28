def create_label_mapping(grid_n):
    label_map = {}
    for i in range(grid_n):
        group_letter = chr(65 + i)  # 'A' to 'H'
        n_elements = 4 if i % 2 == 0 else 3
        
        # Generate labels in ascending order
        suffixes = range(1, n_elements+1) if i == grid_n-1 else range(n_elements, 0, -1)
        
        theta_start = sum(4 if k%2==0 else 3 for k in range(i))
        initial_phi = 31 + sum(3 if k%2==0 else 4 for k in range(i))
        
        for j, suffix in enumerate(suffixes):
            if i == grid_n-1:  # Special handling for last group
                theta = theta_start + (n_elements-1 - j)
                phi = (initial_phi - (n_elements-1)) + j
            else:
                theta = theta_start + j
                phi = initial_phi - j
            
            label = f"{group_letter}{suffix}"
            label_map[label] = (theta, phi)
    
    return label_map
# ## Use this if A1 is at the bottom left corner
# def create_label_mapping(grid_n):
#     """
#     Creates mapping with phi starting at 31 and theta at 0
#     - Phi channels decrease from column base
#     - Theta channels increase from column base
#     - Column bases follow adjusted pattern
#     """
#     label_map = {}
    
#     # Initial bases - swapped values
#     phi_base = 31  # Now phi starts at 31
#     theta_base = 0  # Theta starts at 0
#     prev_phi = phi_base
#     prev_theta = theta_base
    
#     for col in range(grid_n):
#         col_letter = chr(ord('A') + col)
        
#         # Determine number of crosses in column
#         if col % 2 == 0:
#             num_crosses = grid_n // 2
#         else:
#             num_crosses = (grid_n // 2) - 1

#         # Update bases for new column (pattern alternates +4/+3)
#         if col > 0:
#             if col % 2 == 1:  # Odd columns get +4 phi, +3 theta
#                 phi_base = prev_phi + 4
#                 theta_base = prev_theta + 3
#             else:  # Even columns get +3 phi, +4 theta
#                 phi_base = prev_phi + 3
#                 theta_base = prev_theta + 4
#             prev_phi = phi_base
#             prev_theta = theta_base

#         # Assign channel pairs for each cross
#         for cross_num in range(1, num_crosses + 1):
#             label = f"{col_letter}{cross_num}"
#             phi_ch = phi_base - (cross_num - 1)  # Phi decreases
#             theta_ch = theta_base + (cross_num - 1)  # Theta increases
#             label_map[label] = (theta_ch, phi_ch)
    
#     return label_map

# Example usage:
print(create_label_mapping(8))
