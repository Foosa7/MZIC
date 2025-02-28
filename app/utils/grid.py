# app/utils/grid.py
from tkinter import Tk, Canvas, Frame, BOTH, Label, Button, Text, Toplevel, Entry
from collections import defaultdict
import json
import customtkinter as ctk
import tkinter.messagebox as messagebox

class Node:
    """Represents a node."""
    def __init__(self, name, x, y):
        self.name = name  # Name of the node
        self.x = x        # X-coordinate
        self.y = y        # Y-coordinate

class Path:
    """Represents a path (line) connecting two nodes."""
    def __init__(self, node1, node2, line_id):
        self.node1 = node1
        self.node2 = node2
        self.line_id = line_id

class Example(Frame):
    def __init__(self, master=None, grid_n=8, scale=1):
        """
        master: parent widget.
        grid_n: number of columns (and related rows) for the grid.
        scale: scaling factor to adjust the grid's size while keeping the ratios.
        """
        super().__init__(master)
        self.grid_n = grid_n
        self.scale = scale
        self.selection_callback = None  # Callback to update dynamic selection display.
        self.initUI()
        self.input_boxes = {}  # Tracks input boxes by cross label.
        self.cross_selected_count = defaultdict(int)  # Tracks selected path counts per cross.

    def initUI(self):
        self.pack(fill=BOTH, expand=1)
        
        # Control frame (optional)
        # control_frame = Frame(self)
        # control_frame.pack(side='top', fill='x')
        
        # self.coord_label = Label(control_frame, text="X: 0, Y: 0", font=("Arial", 12))
        # self.coord_label.pack(side='left', padx=10, pady=5)
        
        # Create canvas with grey background and no highlight border.
        self.canvas = Canvas(self, bg='grey16', highlightthickness=0)
        
        self.nodes = {}
        self.paths = []
        self.selected_paths = set()
        self.cross_labels = {}
        
        # Base values (for the original 8x8 grid)
        base_horizontal = 100
        base_vertical = 200
        base_arm = 50
        base_start_x = 150
        base_start_y = 80
        
        # Apply the scaling factor (e.g. 0.5 will use half the size)
        horizontal_spacing = base_horizontal * self.scale
        vertical_spacing = base_vertical * self.scale
        arm_length = base_arm * self.scale
        start_x = base_start_x * self.scale
        start_y = base_start_y * self.scale
        
        # Create the grid using the computed parameters.
        self.create_nxn_grid(
            n=self.grid_n, 
            start_x=start_x,
            start_y=start_y,
            horizontal_spacing=horizontal_spacing,
            vertical_spacing=vertical_spacing,
            arm_length=arm_length
        )
        
        # self.canvas.bind("<Motion>", self.show_coordinates)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.pack(fill=BOTH, expand=1)

    # def create_nxn_grid(self, n, start_x, start_y, horizontal_spacing, vertical_spacing, arm_length):
    #     """Creates X shapes with numbered extensions for 8x8 grids."""
    #     # Create all crosses
    #     for col in range(n):
    #         x = start_x + col * horizontal_spacing
    #         letter = chr(ord('A') + col)
    #         if col % 2 == 0:  # Even columns
    #             num_crosses = n // 2
    #             for row in range(num_crosses):
    #                 y = start_y + row * vertical_spacing
    #                 self.create_x_shape(
    #                     center_name=f"X_{col}_{row}",
    #                     x=x, y=y,
    #                     arm_length=arm_length,
    #                     label=f"{letter}{row+1}"
    #                 )
    #         else:  # Odd columns
    #             num_crosses = (n // 2) - 1
    #             for row in range(num_crosses):
    #                 y = start_y + (vertical_spacing // 2) + row * vertical_spacing
    #                 self.create_x_shape(
    #                     center_name=f"X_{col}_{row}",
    #                     x=x, y=y,
    #                     arm_length=arm_length,
    #                     label=f"{letter}{row+1}"
    #                 )

    #     # Add extensions with numbering
    #     self.add_side_extensions(n, col=0, extension=50, side="left")
    #     last_col = n - 1
    #     self.add_side_extensions(n, col=last_col, extension=50, side="right")

    #     # Special handling for second last column outputs
    #     second_last_col = n - 2
    #     if second_last_col % 2 == 0:
    #         max_row = (n // 2) - 1
    #     else:
    #         max_row = (n // 2) - 2

    #     # Create top extension for second last column
    #     top_node_name = f"X_{second_last_col}_0_TR"
    #     if top_node_name in self.nodes:
    #         node = self.nodes[top_node_name]
    #         ext_node = Node(
    #             f"{node.name}_OUTPUT",
    #             node.x + 150,
    #             node.y
    #         )
    #         self.nodes[ext_node.name] = ext_node
    #         self.create_path(node, ext_node)

    #     # Create bottom extension for second last column
    #     bottom_node_name = f"X_{second_last_col}_{max_row}_BR"
    #     if bottom_node_name in self.nodes:
    #         node = self.nodes[bottom_node_name]
    #         ext_node = Node(
    #             f"{node.name}_OUTPUT",
    #             node.x + 150,
    #             node.y
    #         )
    #         self.nodes[ext_node.name] = ext_node
    #         self.create_path(node, ext_node)

    #     # Numbering for special right-side outputs (8x8 only)
    #     if n == 8:
    #         right_outputs = []
    #         # Collect second last column outputs
    #         right_outputs.extend([
    #             self.nodes.get(f"X_{second_last_col}_0_TR_OUTPUT"),
    #             self.nodes.get(f"X_{second_last_col}_{max_row}_BR_OUTPUT")
    #         ])
            
    #         # Collect last column outputs
    #         last_col_nodes = [n for n in self.nodes.values() 
    #                         if f"X_{last_col}_" in n.name and "_OUTPUT" in n.name]
    #         last_col_nodes.sort(key=lambda x: -x.y)  # Top to bottom
            
    #         # Combine all outputs with correct order
    #         sorted_outputs = [
    #             right_outputs[0],        # Second last column top
    #             *last_col_nodes,         # Last column ordered
    #             right_outputs[1]         # Second last column bottom
    #         ]

    #         # Add number labels
    #         for i, node in enumerate(filter(None, sorted_outputs)):
    #             label = 7 + i
    #             # Add text label 25px right of the node
    #             self.canvas.create_text(
    #                 node.x + 25, node.y,
    #                 text=str(label),
    #                 anchor="w",
    #                 fill="black",
    #                 font=("Arial", 10)
    #             )

    #     # Connect even columns
    #     for col in range(0, n, 2):
    #         if col + 2 >= n:
    #             break
    #         # Top connection
    #         self.connect_nodes(
    #             f"X_{col}_0_TR",
    #             f"X_{col+2}_0_TL"
    #         )
    #         # Bottom connection
    #         self.connect_nodes(
    #             f"X_{col}_{(n//2)-1}_BR",
    #             f"X_{col+2}_{(n//2)-1}_BL"
    #         )


    # Original method to create the grid. A1 at the top. ##
    def create_nxn_grid(self, n, start_x, start_y, horizontal_spacing, vertical_spacing, arm_length):
        """Creates X shapes with proper input/output extensions."""
        # Create all crosses.
        for col in range(n):
            x = start_x + col * horizontal_spacing
            letter = chr(ord('A') + col)
            if col % 2 == 0:  # Even columns.
                num_crosses = n // 2
                for row in range(num_crosses):
                    y = start_y + row * vertical_spacing
                    self.create_x_shape(
                        center_name=f"X_{col}_{row}",
                        x=x, y=y,
                        arm_length=arm_length,
                        label=f"{letter}{row+1}"
                    )
            else:  # Odd columns.
                num_crosses = (n // 2) - 1
                for row in range(num_crosses):
                    y = start_y + (vertical_spacing // 2) + row * vertical_spacing
                    self.create_x_shape(
                        center_name=f"X_{col}_{row}",
                        x=x, y=y,
                        arm_length=arm_length,
                        label=f"{letter}{row+1}"
                    )

    # ## New method to create the grid. A1 at the bottom. ##
    # def create_nxn_grid(self, n, start_x, start_y, horizontal_spacing, vertical_spacing, arm_length):
    #     """Creates X shapes with bottom-to-top labeling (A1 at base)"""
    #     for col in range(n):
    #         x = start_x + col * horizontal_spacing
    #         letter = chr(ord('A') + col)
            
    #         if col % 2 == 0:  # Even columns
    #             num_crosses = n // 2
    #             for row in range(num_crosses):
    #                 y = start_y + row * vertical_spacing
    #                 self.create_x_shape(
    #                     center_name=f"X_{col}_{row}",
    #                     x=x, y=y,
    #                     arm_length=arm_length,
    #                     label=f"{letter}{num_crosses - row}"  # Reverse numbering
    #                 )
    #         else:  # Odd columns
    #             num_crosses = (n // 2) - 1
    #             for row in range(num_crosses):
    #                 y = start_y + (vertical_spacing // 2) + row * vertical_spacing
    #                 self.create_x_shape(
    #                     center_name=f"X_{col}_{row}",
    #                     x=x, y=y,
    #                     arm_length=arm_length,
    #                     label=f"{letter}{num_crosses - row}"  # Reverse numbering
    #                 )
                    
        # Add left inputs to first column.
        # self.add_side_extensions(col=0, extension=50, side="left")
        
        # Add right outputs to LAST COLUMN.
        last_col = n - 1
        # self.add_side_extensions(col=last_col, extension=50, side="right")

        # # In create_nxn_grid calls, pass n parameter:
        self.add_side_extensions(n, col=0, extension=50, side="left")
        self.add_side_extensions(n, col=last_col, extension=50, side="right")

        # Add right outputs to second LAST COLUMN (only top and bottom)
        second_last_col = n - 2

        # Determine maximum row based on column parity
        if second_last_col % 2 == 0:  # Even column
            max_row = (n // 2) - 1
        else:  # Odd column
            max_row = (n // 2) - 2

        # # Topmost node (TR of first cross)
        # top_node_name = f"X_{second_last_col}_0_TR"
        # if top_node_name in self.nodes:
        #     node = self.nodes[top_node_name]
        #     ext_node = Node(
        #         f"{node.name}_OUTPUT",
        #         node.x + 150,
        #         node.y
        #     )
        #     self.nodes[ext_node.name] = ext_node
        #     self.create_path(node, ext_node)

        # # Bottommost node (BR of last cross)
        # bottom_node_name = f"X_{second_last_col}_{max_row}_BR"
        # if bottom_node_name in self.nodes:
        #     node = self.nodes[bottom_node_name]
        #     ext_node = Node(
        #         f"{node.name}_OUTPUT",
        #         node.x + 150,
        #         node.y
        #     )
        #     self.nodes[ext_node.name] = ext_node
        #     self.create_path(node, ext_node)


        # Connect even columns.
        for col in range(0, n, 2):
            if col + 2 >= n:
                break
            # Top connection.
            self.connect_nodes(
                f"X_{col}_0_TR",
                f"X_{col+2}_0_TL"
            )
            # Bottom connection.
            self.connect_nodes(
                f"X_{col}_{(n//2)-1}_BR",
                f"X_{col+2}_{(n//2)-1}_BL"
            )

    def add_side_extensions(self, n, col, extension, side):
        """Handles extensions with proper inverted left numbering and special node placement"""
        relevant_nodes = []
        second_last_col = n - 2
        
        # Node collection with precise filtering
        for node in self.nodes.values():
            parts = node.name.split('_')
            if len(parts) < 4: continue
            node_col, direction = int(parts[1]), parts[3]
            
            # Special case: right side of last column (8x8 only)
            if n == 8 and side == "right" and col == second_last_col + 1:
                if node_col in [second_last_col, col] and direction in ["TR", "BR"]:
                    relevant_nodes.append(node)
            # Normal case
            elif node_col == col and ((side == "left" and direction in ["TL", "BL"]) or 
                                    (side == "right" and direction in ["TR", "BR"])):
                relevant_nodes.append(node)

        # Custom sorting logic
        if n == 8 and side == "right" and col == second_last_col + 1:
            # Special right-side handling
            second_last_nodes = [n for n in relevant_nodes if f"X_{second_last_col}" in n.name]
            last_col_nodes = sorted([n for n in relevant_nodes if f"X_{col}_" in n.name], 
                                key=lambda x: x.y)
            
            # Find bottom node using max row calculation
            max_row = max(int(n.name.split('_')[2]) for n in second_last_nodes) if second_last_nodes else 0
            sorted_nodes = [
                next((n for n in second_last_nodes if "_0_TR" in n.name), None),
                *last_col_nodes,
                next((n for n in second_last_nodes if f"_{max_row}_BR" in n.name), None)
            ]
            sorted_nodes = [n for n in sorted_nodes if n]  # Remove None values
        else:
            # Sort nodes by Y-coordinate ascending (top to bottom)
            sorted_nodes = sorted(relevant_nodes, key=lambda x: x.y, reverse=False)

        # Create extensions and labels
        for i, node in enumerate(sorted_nodes):
            # Determine extension parameters
            is_special = f"X_{second_last_col}" in node.name and side == "right"
            ext_length = extension * 3 if is_special else extension
            
            # Calculate extension position
            new_x = node.x + (ext_length if side == "right" else -ext_length)
            ext_node = Node(f"{node.name}_EXT", new_x, node.y)
            self.nodes[ext_node.name] = ext_node
            self.create_path(node, ext_node)

            # Add labels for 8x8 grid
            if n == 8:
                # Calculate label based on side and position
                label = 14 - i if side == "left" else 7 + i
                text_offset = 25 if is_special else 20
                text_x = new_x + (text_offset if side == "right" else -text_offset)
                
                self.canvas.create_text(
                    text_x, node.y,
                    text=str(label),
                    anchor="w" if side == "right" else "e",
                    fill="white",
                    font=("Arial", 12 if is_special else 12, "bold"),
                    tags="io_label"
                )

        # Connect special vertical extensions
        if side == "right" and col == second_last_col and n == 8:
            self.connect_vertical_extensions(col, (n//2)-1, extension*3)


    def connect_vertical_extensions(self, col, max_row, extension):
        """Connects special vertical extensions with proper spacing"""
        # Top connection
        if top_node := self.nodes.get(f"X_{col}_0_TR_EXT"):
            self.create_path(
                self.nodes[f"X_{col}_0_TR"],
                top_node
            )
        
        # Bottom connection
        if bottom_node := self.nodes.get(f"X_{col}_{max_row}_BR_EXT"):
            self.create_path(
                self.nodes[f"X_{col}_{max_row}_BR"],
                bottom_node
            )



    def create_x_shape(self, center_name, x, y, arm_length, label):
        """Creates an X shape with label."""
        self.nodes[center_name] = Node(center_name, x, y)
        self.cross_labels[center_name] = self.canvas.create_text(
            x + arm_length - 20, y,
            text=label,
            anchor='w', font=("Arial", 12), fill="white"
        )

        # # Create top-left dot (added feature)
        # tl_x = x - arm_length
        # tl_y = y - arm_length
        # self.canvas.create_oval(
        #     tl_x - 3, tl_y - 3,  # Coordinates for top-left corner
        #     tl_x + 3, tl_y + 3,  # Coordinates for bottom-right corner
        #     fill="white",         # Match label color
        #     outline="white"       # Remove border
        # )

        # Create arm nodes.
        for suffix, (dx, dy) in {
            "TL": (-arm_length, -arm_length),
            "TR": (arm_length, -arm_length),
            "BL": (-arm_length, arm_length),
            "BR": (arm_length, arm_length)
        }.items():
            arm_name = f"{center_name}_{suffix}"
            self.nodes[arm_name] = Node(arm_name, x + dx, y + dy)
            self.create_path(self.nodes[center_name], self.nodes[arm_name])

    def connect_nodes(self, node1_name, node2_name):
        """Connects two nodes if they exist."""
        if (node1 := self.nodes.get(node1_name)) and (node2 := self.nodes.get(node2_name)):
            self.create_path(node1, node2)

    def create_path(self, node1, node2):
        """Creates a visible path between nodes."""
        line_id = self.canvas.create_line(
            node1.x, node1.y,
            node2.x, node2.y,
            fill="white", width=2
        )
        self.paths.append(Path(node1, node2, line_id))

    def on_canvas_click(self, event):
        """Handles path selection."""
        for path in self.paths:
            coords = self.canvas.coords(path.line_id)
            if len(coords) >= 4 and self.is_point_near_line(event.x, event.y, *coords[:4], 15): # 15 pixels tolerance
                self.toggle_path_selection(path)

    def toggle_path_selection(self, path):
        """Toggles path selection state."""
        adding = path.line_id not in self.selected_paths
        if adding:
            self.canvas.itemconfig(path.line_id, fill="red")
            self.selected_paths.add(path.line_id)
        else:
            self.canvas.itemconfig(path.line_id, fill="white")
            self.selected_paths.remove(path.line_id)
        affected_crosses = set()
        for node in [path.node1, path.node2]:
            cross_label = self.get_cross_label_from_node(node)
            if cross_label:
                affected_crosses.add(cross_label)
        for cross_label in affected_crosses:
            if adding:
                self.cross_selected_count[cross_label] += 1
                if self.cross_selected_count[cross_label] == 1:
                    self.create_input_boxes(cross_label)
            else:
                self.cross_selected_count[cross_label] -= 1
                if self.cross_selected_count[cross_label] == 0:
                    self.delete_input_boxes(cross_label)
        self.update_selection()  # Update dynamic selection display.

    def update_selection(self):
        """Update the selection callback with lines like:
           A1-TL  3, 0
           A1-BR  3, 0
        """
        if not self.selection_callback:
            return
        
        # Dictionary to hold arms for each cross.
        # Keys will be the center text (e.g., "A1") and values will be a set of arm suffixes.
        selected_arms = {}
        
        for path in self.paths:
            if path.line_id in self.selected_paths:
                # For each selected path, determine which of its nodes is the center.
                # We assume the center text is returned by get_cross_label_from_node().
                center1 = self.get_cross_label_from_node(path.node1)
                center2 = self.get_cross_label_from_node(path.node2)
                # We'll check each node; if it has 4 parts then it is an arm,
                # and if the other node's center matches it then we use that arm.
                # (A more robust method might be needed in complex cases.)
                parts1 = path.node1.name.split("_")
                parts2 = path.node2.name.split("_")
                if len(parts1) == 3 and len(parts2) == 4:
                    # node1 is center, node2 is arm.
                    center = center1  # should equal cross label
                    arm = parts2[-1]
                elif len(parts1) == 4 and len(parts2) == 3:
                    center = center2
                    arm = parts1[-1]
                elif len(parts1) == 4 and len(parts2) == 4:
                    # Both are arms. We can choose one, for example the first one.
                    center = self.get_cross_label_from_node(path.node1)
                    arm = parts1[-1]
                else:
                    # Fallback: use center from first node.
                    center = center1
                    arm = ""
                if center:
                    if center not in selected_arms:
                        selected_arms[center] = set()
                    if arm:
                        selected_arms[center].add(arm)
        
        # Now build the output string.
        output_lines = []
        for center, arms in selected_arms.items():
            # Read theta and phi from the input boxes for this cross.
            if center in self.input_boxes:
                theta_val = self.input_boxes[center]['theta_entry'].get().strip() or "0"
                phi_val = self.input_boxes[center]['phi_entry'].get().strip() or "0"
            else:
                theta_val, phi_val = "0", "0"
            for arm in sorted(arms):
                output_lines.append(f"{center}-{arm}  {theta_val}, {phi_val}")
        
        self.selection_callback("\n".join(output_lines))

    def get_path_label(self, path):
        """Creates a label for a given path.
           - Determines the basic label based on the node names.
           - Then, looks up the center cross input boxes and appends their theta and phi values.
        """
        node1, node2 = path.node1, path.node2
        label = None
        # Check for extension nodes first.
        for node in [node1, node2]:
            if "INPUT" in node.name or "OUTPUT" in node.name:
                parts = node.name.split("_")
                label = f"{chr(65 + int(parts[1]))}{int(parts[2]) + 1}-{parts[3]}"
                break
        if not label:
            parts1 = node1.name.split("_")
            parts2 = node2.name.split("_")
            # Both nodes are arms (4 parts)
            if len(parts1) == 4 and len(parts2) == 4:
                if parts1[:3] == parts2[:3]:
                    label = f"{chr(65 + int(parts1[1]))}{int(parts1[2]) + 1}-{parts1[3]} to {parts2[3]}"
                else:
                    label = f"{chr(65 + int(parts1[1]))}{int(parts1[2]) + 1}-{parts1[3]} to {chr(65 + int(parts2[1]))}{int(parts2[2]) + 1}-{parts2[3]}"
            # One node is an arm and the other is the center.
            elif len(parts1) == 4 and len(parts2) == 3:
                center = self.get_cross_label_from_node(node2)
                label = f"{chr(65 + int(parts1[1]))}{int(parts1[2]) + 1}-{parts1[3]} to {center}"
            elif len(parts1) == 3 and len(parts2) == 4:
                center = self.get_cross_label_from_node(node1)
                label = f"{center} to {chr(65 + int(parts2[1]))}{int(parts2[2]) + 1}-{parts2[3]}"
            else:
                label = self.get_cross_label_from_node(node1)
                if not label:
                    label = "Unknown"
        # Now, get the center cross text (e.g. "A1") using get_cross_label_from_node.
        center_text = self.get_cross_label_from_node(node1)
        # If found and input boxes exist, read their values.
        if center_text is not None and center_text in self.input_boxes:
            theta_val = self.input_boxes[center_text]['theta_entry'].get().strip()
            phi_val = self.input_boxes[center_text]['phi_entry'].get().strip()
            # Use defaults if values are empty.
            if not theta_val:
                theta_val = "0"
            if not phi_val:
                phi_val = "0"
            label = label + "\n" + f"{theta_val}, {phi_val}"
        else:
            label = label + "\n0, 0"
        return label


    def get_cross_label_from_node(self, node):
        """Retrieves the cross label associated with an arm or center node."""
        parts = node.name.split('_')
        if parts[0] != 'X':
            return None
        if len(parts) == 3:
            cross_center_name = node.name
        elif len(parts) == 4:
            cross_center_name = '_'.join(parts[:3])
        else:
            return None
        text_id = self.cross_labels.get(cross_center_name)
        if not text_id:
            return None
        return self.canvas.itemcget(text_id, 'text')

    def create_input_boxes(self, cross_label):
        """Creates theta and phi input boxes next to the cross label, pre-populated with default data."""
        cross_center_name = None
        for center, text_id in self.cross_labels.items():
            if self.canvas.itemcget(text_id, 'text') == cross_label:
                cross_center_name = center
                break
        if not cross_center_name:
            return
        text_id = self.cross_labels[cross_center_name]
        x, y = self.canvas.coords(text_id)
        input_x = x + 30  # Adjust as needed.
        # Theta input.
        theta_label_id = self.canvas.create_text(input_x, y - 20, text="θ:", anchor='w', font=("Arial", 14), fill="white")
        theta_entry = Entry(self.canvas, width=6)
        theta_entry_id = self.canvas.create_window(input_x + 20, y - 20, window=theta_entry, anchor='w')
        # Phi input.
        phi_label_id = self.canvas.create_text(input_x, y + 20, text="φ:", anchor='w', font=("Arial", 14), fill="white")
        phi_entry = Entry(self.canvas, width=6)
        phi_entry_id = self.canvas.create_window(input_x + 20, y + 20, window=phi_entry, anchor='w')
        
        # Bind key-release events so that when the user types, update_selection() is called.
        theta_entry.bind("<KeyRelease>", lambda event: self.update_selection())
        phi_entry.bind("<KeyRelease>", lambda event: self.update_selection())
        
        self.input_boxes[cross_label] = {
            'theta_entry': theta_entry,
            'phi_entry': phi_entry,
            'theta_label_id': theta_label_id,
            'phi_label_id': phi_label_id,
            'theta_entry_id': theta_entry_id,
            'phi_entry_id': phi_entry_id
        }


    def delete_input_boxes(self, cross_label):
        """Removes theta and phi input boxes for the given cross label."""
        if cross_label in self.input_boxes:
            boxes = self.input_boxes[cross_label]
            self.canvas.delete(boxes['theta_label_id'])
            self.canvas.delete(boxes['phi_label_id'])
            self.canvas.delete(boxes['theta_entry_id'])
            self.canvas.delete(boxes['phi_entry_id'])
            boxes['theta_entry'].destroy()
            boxes['phi_entry'].destroy()
            del self.input_boxes[cross_label]

    def is_point_near_line(self, px, py, x1, y1, x2, y2, threshold):
        """Checks if point is near a line segment."""
        dx, dy = x2 - x1, y2 - y1
        if dx == dy == 0:
            return ((px-x1)**2 + (py-y1)**2)**0.5 <= threshold
        t = ((px-x1)*dx + (py-y1)*dy) / (dx**2 + dy**2)
        t = max(0, min(1, t))
        closest_x = x1 + t*dx
        closest_y = y1 + t*dy
        return ((px-closest_x)**2 + (py-closest_y)**2)**0.5 <= threshold

    def show_coordinates(self, event):
        """Updates coordinate display."""
        self.coord_label.config(text=f"X: {event.x}, Y: {event.y}")
    
    def export_paths_json(self):
        """
        Exports selected paths as a JSON string.
        Creates a dictionary keyed by the center (e.g. "A1").
        Each value is a dict with keys:
           - "arms": a list of arm suffixes selected (e.g. ["TL", "BR"])
           - "theta": the current value from the theta input box (default "0")
           - "phi": the current value from the phi input box (default "0")
        """
        export_data = {}
        for path in self.paths:
            if path.line_id in self.selected_paths:
                # Determine the center text for this path.
                center = self.get_cross_label_from_node(path.node1) or self.get_cross_label_from_node(path.node2)
                if not center:
                    continue
                # Determine the arm associated with this path.
                parts1 = path.node1.name.split("_")
                parts2 = path.node2.name.split("_")
                arm = None
                if len(parts1) == 4 and len(parts2) == 3:
                    arm = parts1[-1]
                elif len(parts1) == 3 and len(parts2) == 4:
                    arm = parts2[-1]
                elif len(parts1) == 4 and len(parts2) == 4:
                    arm = parts1[-1]
                if center not in export_data:
                    # If input boxes exist for this center, get their values; otherwise use defaults.
                    if center in self.input_boxes:
                        theta_val = self.input_boxes[center]['theta_entry'].get().strip() or "0"
                        phi_val = self.input_boxes[center]['phi_entry'].get().strip() or "0"
                    else:
                        theta_val, phi_val = "0", "0"
                    export_data[center] = {"arms": [], "theta": theta_val, "phi": phi_val}
                if arm and arm not in export_data[center]["arms"]:
                    export_data[center]["arms"].append(arm)
        return json.dumps(export_data)

    def import_paths_json(self, json_str):
        """
        Imports path selection from a JSON string.
        The JSON is expected to be a dictionary with keys equal to the center (e.g. "A1")
        and values containing:
           - "arms": list of arms to select (e.g. ["TL", "BR"])
           - "theta": string value for theta
           - "phi": string value for phi
        For each center, all paths that match a selected arm will be re‑selected,
        and the corresponding input boxes will be updated (or created).
        """
        try:
            imported = json.loads(json_str)
        except Exception as e:
            print("Invalid JSON:", e)
            return

        # Clear current selection.
        for path in self.paths:
            if path.line_id in self.selected_paths:
                self.canvas.itemconfig(path.line_id, fill="white")
        self.selected_paths.clear()

        # For each center in the imported data...
        for center, data in imported.items():
            arms = data.get("arms", [])
            theta_val = data.get("theta", "0")
            phi_val = data.get("phi", "0")
            # Loop over all paths and re-select those that match.
            for path in self.paths:
                # Use the center from either node.
                center_from_node = self.get_cross_label_from_node(path.node1) or self.get_cross_label_from_node(path.node2)
                if center_from_node != center:
                    continue
                # Determine the arm for this path.
                parts1 = path.node1.name.split("_")
                parts2 = path.node2.name.split("_")
                arm = None
                if len(parts1) == 4 and len(parts2) == 3:
                    arm = parts1[-1]
                elif len(parts1) == 3 and len(parts2) == 4:
                    arm = parts2[-1]
                elif len(parts1) == 4 and len(parts2) == 4:
                    arm = parts1[-1]
                if arm and arm in arms:
                    self.canvas.itemconfig(path.line_id, fill="red")
                    self.selected_paths.add(path.line_id)
            # Ensure input boxes for this center exist; if not, create them.
            if center not in self.input_boxes:
                self.create_input_boxes(center)
            if center in self.input_boxes:
                self.input_boxes[center]['theta_entry'].delete(0, "end")
                self.input_boxes[center]['theta_entry'].insert(0, theta_val)
                self.input_boxes[center]['phi_entry'].delete(0, "end")
                self.input_boxes[center]['phi_entry'].insert(0, phi_val)
        self.update_selection()

def main():
    root = Tk()
    Example()
    # root.geometry("1400x1000")
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}") #+-10+-5
    root.mainloop()

if __name__ == '__main__':
    main()
