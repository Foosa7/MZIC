# app/utils/grid.py
from app.utils.appdata import AppData
from tkinter import Tk, Canvas, Frame, BOTH, Label, Button, Text, Toplevel, Entry
from collections import defaultdict
import json
import customtkinter as ctk
import tkinter.messagebox as messagebox
import logging

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
        self.last_selection = {"cross": None, "arm": None}  
        self.io_config = "None"  # Default I/O configuration

    def initUI(self):
        self.pack(fill=BOTH, expand=1)
        self.canvas = Canvas(self, bg='grey16', highlightthickness=0)
        self.nodes = {}
        self.paths = []
        self.selected_paths = set()
        self.cross_labels = {}

        # Set geometry based on grid size
        if self.grid_n == 8:
            base_horizontal = 100
            base_vertical = 200
            base_arm = 50
            base_start_x = 150
            base_start_y = 80
        elif self.grid_n == 12:
            base_horizontal = 100*0.8
            base_vertical = 200*0.8
            base_arm = 50*0.8
            base_start_x = 130
            base_start_y = 70
        else:
            # Fallback/default values
            base_horizontal = 100
            base_vertical = 200
            base_arm = 50
            base_start_x = 150
            base_start_y = 80

        # Apply the scaling factor (if you want to keep it for other cases)
        horizontal_spacing = base_horizontal * self.scale
        vertical_spacing = base_vertical * self.scale
        arm_length = base_arm * self.scale
        start_x = base_start_x * self.scale
        start_y = base_start_y * self.scale

        self.create_nxn_grid(
            n=self.grid_n,
            start_x=start_x,
            start_y=start_y,
            horizontal_spacing=horizontal_spacing,
            vertical_spacing=vertical_spacing,
            arm_length=arm_length
        )

        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.pack(fill=BOTH, expand=1)

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
            if n in [8, 12] and side == "right" and col == second_last_col + 1:
                if node_col in [second_last_col, col] and direction in ["TR", "BR"]:
                    relevant_nodes.append(node)
            # Normal case
            elif node_col == col and ((side == "left" and direction in ["TL", "BL"]) or 
                                    (side == "right" and direction in ["TR", "BR"])):
                relevant_nodes.append(node)

        # Custom sorting logic
        if n in [8, 12] and side == "right" and col == second_last_col + 1:
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
            if n == 8 and is_special:
                ext_length = extension * 3
            elif n == 12 and is_special:
                ext_length = extension * 2.6
            else:
                ext_length = extension
            
            # Calculate extension position
            new_x = node.x + (ext_length if side == "right" else -ext_length)
            ext_node = Node(f"{node.name}_EXT", new_x, node.y)
            self.nodes[ext_node.name] = ext_node
            self.create_path(node, ext_node)

            # Add labels for grid
            if n == 8:
                label = 14 - i if side == "left" else 7 + i
                self._draw_side_label(is_special, label, side, new_x, node.y)
            elif n == 12:
                label = 3 + i if side == "left" else 14 - i
                self._draw_side_label(is_special, label, side, new_x, node.y)

        if side == "right" and col == second_last_col and n == 8:
            self.connect_vertical_extensions(col, (n // 2) - 1, extension * 3)
        elif side == "right" and col == second_last_col and n == 12:
            self.connect_vertical_extensions(col, (n // 2) - 1, extension * 3)
            
    # def _draw_side_label(self, is_special, label, side, new_x, node_y):
    #     """Draw the numeric label for a side extension, used by add_side_extensions"""
    #     #text_offset = 15 if is_special else 10
    #     text_offset = 15
    #     text_x = new_x + (text_offset if side == "right" else -text_offset)
    #     self.canvas.create_text(
    #         text_x,
    #         node_y,
    #         text=str(label),
    #         anchor="w" if side == "right" else "e",
    #         fill="white",
    #         font=("Arial", 12 if is_special else 12, "bold"),
    #         tags="io_label"
    #     )

    def _draw_side_label(self, is_special, label, side, new_x, node_y):
        """Draws and binds a clickable numeric label for a side extension."""
        text_offset = 15
        text_x = new_x + (text_offset if side == "right" else -text_offset)
        # Create a unique tag for each label based on side and label number.
        label_tag = f"input_label_{label}" if side == "left" else f"output_label_{label}"
        
        # Create the text on the canvas with both a common tag and a unique tag.
        text_item = self.canvas.create_text(
            text_x,
            node_y,
            text=str(label),
            anchor="w" if side == "right" else "e",
            fill="white",
            font=("Arial", 12 if is_special else 12, "bold"),
            tags=("io_label", label_tag)
        )
        
        # Bind a click event to the label text so it becomes selectable.
        self.canvas.tag_bind(label_tag, "<Button-1>", lambda event, tag=label_tag: self.on_side_label_click(event, tag))


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
        self.cross_labels[center_name] = None  # Initialize label ID
        label_id = self.canvas.create_text(
            x + arm_length - 20, y,
            text=label,
            anchor='w', font=("Arial", 12), fill="white"
        )
        self.cross_labels[center_name] = label_id
        self.canvas.tag_bind(label_id, "<Button-1>", lambda event, lbl=label: self.on_label_click(lbl, label_id))


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

    def on_label_click(self, label, label_id):
        """Handles label selection and stores selected labels in AppData."""
        if not hasattr(AppData, "selected_labels"):
            AppData.selected_labels = set()
        if label in AppData.selected_labels:
            AppData.selected_labels.remove(label)
            self.canvas.itemconfig(label_id, fill="white")
        else:
            AppData.selected_labels.add(label)
            self.canvas.itemconfig(label_id, fill="red")
        #logging.info("Selected labels:", AppData.selected_labels)

    def get_cross_modes(self):
        """Returns a dict mapping cross labels to their selection type (bar/cross/split)."""
        cross_arms = defaultdict(set)
        
        # Collect selected arms per cross.
        for path in self.paths:
            if path.line_id in self.selected_paths:
                center, arm = self._parse_path_components(path)
                if center and arm:
                    # Handle arm pairs (like "TL-BR") from cross connections.
                    if '-' in arm:
                        cross_arms[center].update(arm.split('-'))
                    else:
                        cross_arms[center].add(arm)

        # Determine mode for each cross.
        modes = {}
        for cross, arms in cross_arms.items():
            arm_set = set(arms)
            if len(arm_set) != 2 and len(arm_set) != 3:
                continue  # Only consider pairs or triplets.
            if arm_set in [{'BR', 'BL'}, {'TR', 'TL'}]:
                modes[cross] = 'bar'
            elif arm_set in [{'TL', 'BR'}, {'TR', 'BL'}]:
                modes[cross] = 'cross'
            elif arm_set in [{'TR', 'BR', 'TL'}, {'TR', 'BR', 'BL'}]:  
                modes[cross] = 'split'
        
        return modes



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

    # def on_canvas_click(self, event):
    #     """Handles path selection."""
    #     for path in self.paths:
    #         coords = self.canvas.coords(path.line_id)
    #         if len(coords) >= 4 and self.is_point_near_line(event.x, event.y, *coords[:4], 15):  # 15 pixels tolerance
    #             self.toggle_path_selection(path)

    def on_canvas_click(self, event):
        """Handles path selection."""
        # Use 10 px tolerance if grid_n is 12, else 15
        tolerance = 10 if self.grid_n == 12 else 15
        for path in self.paths:
            coords = self.canvas.coords(path.line_id)
            if len(coords) >= 4 and self.is_point_near_line(event.x, event.y, *coords[:4], tolerance):
                self.toggle_path_selection(path)

    def on_side_label_click(self, event, label_tag):
        """Handles click on a side label by turning it red and calling the appropriate handler."""
        # Change the label color to red.
        self.canvas.itemconfig(label_tag, fill="red")
        
        # Determine if it's an input or output label and extract the label number.
        if label_tag.startswith("input_label_"):
            label_number = label_tag.split("input_label_")[-1]
            # Call your function that handles left-side input labels.
            self.handle_input_label_selection(label_number)
        elif label_tag.startswith("output_label_"):
            label_number = label_tag.split("output_label_")[-1]
            # Call your function that handles right-side output labels.
            self.handle_output_label_selection(label_number)

    # Multiple selection of output labels 
    def handle_input_label_selection(self, label_number):
        # Map label number to pin index
        pin_map = {
            "7": 7,
            "8": 6,
            "9": 5,
            "10": 4,
            "11": 3,
            "12": 2,
            "13": 1,
            "14": 0
        }

        if label_number not in pin_map:
            return

        in_pin_idx = pin_map[label_number]
        label_tag = f"input_label_{label_number}"
        prev_selected_idx = None  # ensure it's defined

        # Deselect previously selected pin (if any)
        if AppData.selected_input_pins:
            prev_selected_idx = next(iter(AppData.selected_input_pins))
            AppData.selected_input_pins.clear()

            # Find the corresponding label number for previous pin (reverse map)
            for k, v in pin_map.items():
                if v == prev_selected_idx:
                    prev_label_tag = f"input_label_{k}"
                    self.canvas.itemconfig(prev_label_tag, fill="white")
                    break

        # If the clicked pin was already selected, it was just unselected — so we're done
        if in_pin_idx == prev_selected_idx:
            logging.info(f"Input Unpinned channel {in_pin_idx}")
            return

        # Otherwise, select the new pin
        AppData.selected_input_pins.add(in_pin_idx)
        self.canvas.itemconfig(label_tag, fill="red")
        logging.info(f"Input Pinned channel {in_pin_idx}")


    def handle_output_label_selection(self, label_number):
        # Map label number to pin index
        pin_map = {
            "7": 7,
            "8": 6,
            "9": 5,
            "10": 4,
            "11": 3,
            "12": 2,
            "13": 1,
            "14": 0
        }

        if label_number not in pin_map:
            return

        in_pin_idx = pin_map[label_number]
        label_tag = f"output_label_{label_number}"
        prev_selected_idx = None  # ensure it's defined

        # Deselect previously selected pin (if any)
        if AppData.selected_output_pins:
            prev_selected_idx = next(iter(AppData.selected_output_pins))
            AppData.selected_output_pins.clear()

            # Find the corresponding label number for previous pin (reverse map)
            for k, v in pin_map.items():
                if v == prev_selected_idx:
                    prev_label_tag = f"output_label_{k}"
                    self.canvas.itemconfig(prev_label_tag, fill="white")
                    break

        # If the clicked pin was already selected, it was just unselected — so we're done
        if in_pin_idx == prev_selected_idx:
            logging.info(f"Output Unpinned channel {in_pin_idx}")
            return

        # Otherwise, select the new pin
        AppData.selected_output_pins.add(in_pin_idx)
        self.canvas.itemconfig(label_tag, fill="red")
        logging.info(f"Output Pinned channel {in_pin_idx}")


    # def handle_output_label_selection(self, label_number):
    #     # For instance, pin_map = {"7": 0, "8": 1, "9": 2, ...} to ai channels
    #     pin_map = {
    #         "7": 0,
    #         "8": 1,
    #         "9": 2,
    #         "10": 3,
    #         "11": 4,
    #         "12": 5,
    #         "13": 6,
    #         "14": 7
    #     }

    #     if label_number not in pin_map:
    #         return
        
    #     out_pin_idx = pin_map[label_number]
    #     label_tag = f"output_label_{label_number}"

    #     if out_pin_idx in AppData.selected_output_pins:
    #         # Unpin
    #         AppData.selected_output_pins.remove(out_pin_idx)
    #         print(f"Output Unpinned channel {out_pin_idx}")
    #         # revert color to default (white)
    #         self.canvas.itemconfig(label_tag, fill="white")
    #     else:
    #         # Pin
    #         AppData.selected_output_pins.add(out_pin_idx)
    #         print(f"Output Pinned channel {out_pin_idx}")

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
                    # Update the input box now that a new arm was added.
                    self.update_input_box_mode(cross_label)
            else:
                self.cross_selected_count[cross_label] -= 1
                if self.cross_selected_count[cross_label] == 0:
                    self.delete_input_boxes(cross_label)
                else:
                    self.update_input_box_mode(cross_label)

        if adding:
            center, arm = self._parse_path_components(path)
            if center and arm:
                self.last_selection = {"cross": center, "arm": arm}
                AppData.update_last_selection(center, arm)  # Keep synced with AppData
                modes = self.get_cross_modes()
                AppData.io_config = modes
                self.event_generate("<<SelectionUpdated>>")  # Trigger update event
                self.update_selection()



    def update_input_box_mode(self, visible_label):
        """Updates the theta input box for the given cross (by visible label) with the default value.
        Inserts 1 if mode is 'bar' and 2 if mode is 'cross_state'."""
        if visible_label not in self.input_boxes:
            return
        modes = self.get_cross_modes()  # modes keyed by visible labels (e.g. "A1", "A2")
        mode = modes.get(visible_label)
        theta_entry = self.input_boxes[visible_label]['theta_entry']
        
        # Clear any current value.
        theta_entry.delete(0, "end")
        
        if mode == 'bar':
            theta_entry.insert(0, "1")
            logging.info(f"{visible_label}: Bar mode detected. Inserting 1.")
        elif mode == 'cross':
            theta_entry.insert(0, "0")
            logging.info(f"{visible_label}: Cross mode detected. Inserting 2.")
        elif mode == 'split':
            theta_entry.insert(0, "0.5")
            logging.info(f"{visible_label}: Split mode detected. Inserting 1.5.")            
        else:
            logging.info(f"{visible_label}: No matching mode. Mode value: {mode}")



    def get_last_selection(self):
        """Public method to access last selection"""
        return self.last_selection.copy()

    def import_paths_json(self, json_str):
        """Existing import method"""
        # Add this at the end to preserve selection after import
        if self.last_selection['cross'] and self.last_selection['arm']:
            self._apply_last_selection()

    def _apply_last_selection(self):
        """Internal method to highlight last selected path"""
        for path in self.paths:
            center, arm = self._parse_path_components(path)
            if (center == self.last_selection['cross'] and 
                arm == self.last_selection['arm']):
                self.toggle_path_selection(path)
                break

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

    def _parse_path_components(self, path):
        """Improved arm detection with extension support"""
        node1, node2 = path.node1, path.node2
        parts1 = node1.name.split('_')
        parts2 = node2.name.split('_')

        # Case 1: Direct center-to-arm connection
        if len(parts1) == 3 and len(parts2) == 4:
            return self.get_cross_label_from_node(node1), parts2[-1]
        if len(parts1) == 4 and len(parts2) == 3:
            return self.get_cross_label_from_node(node2), parts1[-1]

        # Case 2: Arm-to-arm connection (same cross)
        if len(parts1) == 4 and len(parts2) == 4 and parts1[:3] == parts2[:3]:
            return self.get_cross_label_from_node(node1), f"{parts1[-1]}-{parts2[-1]}"

        # Case 3: Input/output extensions
        ext_parts = [p for p in [parts1, parts2] if 'EXT' in p]
        if ext_parts:
            ext_part = ext_parts[0]
            base_part = parts2 if ext_part is parts1 else parts1
            if len(base_part) == 4:
                return self.get_cross_label_from_node(self.nodes['_'.join(base_part[:3])]), base_part[-1]

        # Case 4: Cross-column connections
        if len(parts1) == 4 and len(parts2) == 4:
            return (
                f"{self.get_cross_label_from_node(node1)}-{self.get_cross_label_from_node(node2)}",
                f"{parts1[-1]}-{parts2[-1]}"
            )

        return None, None

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
        # Determine the center key and the actual visible label.
        if cross_label in self.cross_labels:
            # cross_label is actually the internal key (like "X_0_0")
            center_key = cross_label
            actual_label = self.canvas.itemcget(self.cross_labels[center_key], 'text')
        else:
            # Otherwise, search for a key whose visible text equals cross_label.
            center_key = None
            for key, text_id in self.cross_labels.items():
                if self.canvas.itemcget(text_id, 'text') == cross_label:
                    center_key = key
                    break
            if not center_key:
                logging.info("No center key found for", cross_label)
                return
            actual_label = cross_label

        text_id = self.cross_labels[center_key]
        x, y = self.canvas.coords(text_id)
        input_x = x + 30  # Adjust as needed.
        
        # Theta input.
        theta_label_id = self.canvas.create_text(input_x, y - 20, text="θ:", anchor='w', font=("Arial", 14), fill="white")
        theta_entry = Entry(self.canvas, width=6)
        theta_entry_id = self.canvas.create_window(input_x + 20, y - 20, window=theta_entry, anchor='w')
        
        # Get the mode using the visible label (e.g. "A1")
        modes = self.get_cross_modes()  # modes keyed by visible labels (like "A1", "A2", etc.)
        mode = modes.get(actual_label)
        logging.info(f"Mode for {actual_label} is: {mode}")
        
        if mode == 'bar':
            theta_entry.insert(0, "1")
            logging.info("Bar")
        elif mode == 'cross':
            theta_entry.insert(0, "2")
            logging.info("Cross")
        else:
            logging.info(f"No matching mode for {actual_label}. Mode value: {mode}")
        
        # Phi input.
        phi_label_id = self.canvas.create_text(input_x, y + 20, text="φ:", anchor='w', font=("Arial", 14), fill="white")
        phi_entry = Entry(self.canvas, width=6)
        phi_entry_id = self.canvas.create_window(input_x + 20, y + 20, window=phi_entry, anchor='w')
        
        # Bind key-release events so that when the user types, update_selection() is called.
        theta_entry.bind("<KeyRelease>", lambda event: self.update_selection())
        phi_entry.bind("<KeyRelease>", lambda event: self.update_selection())
        
        # Store the input boxes under the visible label.
        self.input_boxes[actual_label] = {
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
    
    # def export_paths_json(self):
    #     """
    #     Exports selected paths as a JSON string.
    #     Creates a dictionary keyed by the center (e.g. "A1").
    #     Each value is a dict with keys:
    #        - "arms": a list of arm suffixes selected (e.g. ["TL", "BR"])
    #        - "theta": the current value from the theta input box (default "0")
    #        - "phi": the current value from the phi input box (default "0")
    #     """
    #     export_data = {}
    #     for path in self.paths:
    #         if path.line_id in self.selected_paths:
    #             # Determine the center text for this path.
    #             center = self.get_cross_label_from_node(path.node1) or self.get_cross_label_from_node(path.node2)
    #             if not center:
    #                 continue
    #             # Determine the arm associated with this path.
    #             parts1 = path.node1.name.split("_")
    #             parts2 = path.node2.name.split("_")
    #             arm = None
    #             if len(parts1) == 4 and len(parts2) == 3:
    #                 arm = parts1[-1]
    #             elif len(parts1) == 3 and len(parts2) == 4:
    #                 arm = parts2[-1]
    #             elif len(parts1) == 4 and len(parts2) == 4:
    #                 arm = parts1[-1]
    #             if center not in export_data:
    #                 # If input boxes exist for this center, get their values; otherwise use defaults.
    #                 if center in self.input_boxes:
    #                     theta_val = self.input_boxes[center]['theta_entry'].get().strip() or "0"
    #                     phi_val = self.input_boxes[center]['phi_entry'].get().strip() or "0"
    #                 else:
    #                     theta_val, phi_val = "0", "0"
    #                 export_data[center] = {"arms": [], "theta": theta_val, "phi": phi_val}
    #             if arm and arm not in export_data[center]["arms"]:
    #                 export_data[center]["arms"].append(arm)
    #     return json.dumps(export_data)

    def export_paths_json(self):
        """
        Exports selected paths as a JSON string.
        Returns a dictionary with:
          - Top-level "input_pin" and "output_pin"
          - Per-center path data with:
              - "arms": list of arm suffixes (e.g. ["TL", "BR"])
              - "theta": phase theta (string)
              - "phi": phase phi (string)
        """
        input_pin = next(iter(AppData.selected_input_pins), None)
        output_pin = next(iter(AppData.selected_output_pins), None)

        export_data = {
            #"input_pin": input_pin,
            #"output_pin": output_pin
        }

        for path in self.paths:
            if path.line_id in self.selected_paths:
                center = self.get_cross_label_from_node(path.node1) or self.get_cross_label_from_node(path.node2)
                if not center:
                    continue

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
                    if center in self.input_boxes:
                        theta_val = self.input_boxes[center]['theta_entry'].get().strip() or "0"
                        phi_val = self.input_boxes[center]['phi_entry'].get().strip() or "0"
                    else:
                        theta_val, phi_val = "0", "0"

                    export_data[center] = {
                        "arms": [],
                        "theta": theta_val,
                        "phi": phi_val
                    }

                if arm and arm not in export_data[center]["arms"]:
                    export_data[center]["arms"].append(arm)

        return json.dumps(export_data, indent=2)



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
            imported = json.loads(json_str) #default_json_grid 
        except Exception as e:
            logging.error("Invalid JSON:", e)
            return

        # Clear current selection.
        for path in self.paths:
            if path.line_id in self.selected_paths:
                self.canvas.itemconfig(path.line_id, fill="white")
                self.toggle_path_selection(path)  # Clear existing
                self.toggle_path_selection(path)  # Re-apply with new data                
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

        self.event_generate("<<SelectionUpdated>>")  # Add event trigger        
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