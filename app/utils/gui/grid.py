# app/utils/grid.py
from app.utils.appdata import AppData
from tkinter import Tk, Canvas, Frame, BOTH, Label, Button, Text, Toplevel, Entry
from collections import defaultdict
import json
import customtkinter as ctk
import tkinter.messagebox as messagebox
import logging, os
from datetime import datetime

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
    def __init__(self, master=None, grid_n=12, scale=1, calibration_json=None, get_cross_modes_func=None, auto_calibrate_callback=None):

        """
        master: parent widget.
        grid_n: number of columns (and related rows) for the grid.
        scale: scaling factor to adjust the grid's size while keeping the ratios.
        """
        super().__init__(master)
        # if calibration_json and get_cross_modes_func:
        #     self.step_lines = convert_calibration_to_grid_inline(
        #         calibration_json, get_cross_modes_func)
        # else:
        self.step_lines = []    
        self.all_steps = []    
        self.playing = False
        self.auto_calibrate_callback = auto_calibrate_callback
        self.current_step = 0
        self.edit_mode = False  # Start in edit mode  
        self.grid_n = grid_n
        self.scale = scale
        self.selection_callback = None  # Callback to update dynamic selection display.
        self.initUI()
        self.input_boxes = {}  # Tracks input boxes by cross label.
        self.cross_selected_count = defaultdict(int)  # Tracks selected path counts per cross.
        self.last_selection = {"cross": None, "arm": None}  
        self.io_config = "None"  # Default I/O configuration

    def initUI(self):
        self.configure(bg='grey16')
        self.pack(fill=BOTH, expand=1)
        self.canvas = Canvas(self, bg='grey16', highlightthickness=0)
        self.nodes = {}
        self.paths = []
        self.selected_paths = set()
        self.cross_labels = {}


        ctrl = Frame(self, bg='grey16')
        ctrl.pack(side='bottom', fill='x', pady=10)

        # left counter
        ctrl.grid_columnconfigure(1, weight=1)
        self.step_label = ctk.CTkButton(
            ctrl,
            text=f"Step {self.current_step}/{len(self.step_lines)}",
            width=80, corner_radius=6,
            fg_color=None, hover=False, state="enabled"
        )
        self.step_label.grid(row=0, column=0, padx=10)

        # center nav
        nav_frame = Frame(ctrl, bg='grey16')
        nav_frame.grid(row=0, column=1)
        self.back_btn = ctk.CTkButton(nav_frame, text="⏮ Back", width=80, command=self.decrement_step, fg_color="transparent")
        self.back_btn.pack(side='left', padx=5)
        # self.play_btn = ctk.CTkButton(nav_frame, text="▶ Play", width=80, command=self.toggle_play, fg_color="transparent")
        # ▶ Play now either starts grid‐stepping or runs auto‐calibration
        self.play_btn = ctk.CTkButton(
            nav_frame,
            text="▶ Play",
            width=80,
            command=self._on_play_clicked,
            fg_color="transparent"
        )

    
        self.play_btn.pack(side='left', padx=5)
        self.next_btn = ctk.CTkButton(
            nav_frame,
            text="Next ⏭",
            width=80,
            command=self.next_step,
            text_color="white",
            fg_color="transparent"

        )
        self.next_btn.pack(side='left', padx=5)
        self.bind_all("<space>", lambda e: self.next_btn.invoke())


        # —— save button on the right ——
        self.mode_btn = ctk.CTkButton(
            ctrl,
            text="👁️ View",              # Start in view mode
            width=80,
            corner_radius=6,
            command=self.toggle_edit_mode
        )
        self.mode_btn.grid(row=0, column=2, padx=10)

        # track the mode
        self.edit_mode = False     # = View mode

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

            # figure out this node’s numeric label BEFORE drawing
            if n == 8:
                label = 14 - i if side == "left" else 7 + i
            elif n == 12:
                label = i + 1 if side == "left" else i + 1
            else:
                # skip any unexpected n
                continue


            # self.create_path(node, ext_node)
            ext_path = self.create_path(node, ext_node)
            line_id   = ext_path.line_id
            label_tag = f"{'input' if side=='left' else 'output'}_label_{label}"
            self.canvas.addtag_withtag(label_tag, line_id)

            # Bind clicks on the line (via its tag) to the same handler as the text
            self.canvas.tag_bind(
                label_tag,
                "<Button-1>",
                lambda event, tag=label_tag: self.on_side_label_click(event, tag)
            )


            # Add labels for grid
            if n == 8:
                label = 14 - i if side == "left" else 7 + i
                self._draw_side_label(is_special, label, side, new_x, node.y)
            elif n == 12:
                label = i + 1 if side == "left" else i + 1
                self._draw_side_label(is_special, label, side, new_x, node.y)
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
        """
        Only one cross label may be selected; clicking the same label again deselects it.
        """
        # If this label is already selected → unselect everything
        if AppData.selected_label == label:
            # 1) clear highlight
            for text_id in self.cross_labels.values():
                self.canvas.itemconfig(text_id, fill="white")
            # 2) clear selection
            AppData.selected_label = ""
            # 3) update AppData.last_selected to no cross
            AppData.update_last_selection("", None)
            return

        # Otherwise, select this one and clear any prior
        for text_id in self.cross_labels.values():
            self.canvas.itemconfig(text_id, fill="white")

        self.canvas.itemconfig(label_id, fill="red")
        AppData.selected_label = label
        AppData.update_last_selection(label, None)


    def get_cross_modes(self):
        """Returns a dict mapping cross labels to their selection type (bar/cross/split/arbitrary)."""
        cross_arms = defaultdict(set)
        for path in self.paths:
            if path.line_id in self.selected_paths:
                center, arm = self._parse_path_components(path)
                if center and arm:
                    if '-' in arm:
                        cross_arms[center].update(arm.split('-'))
                    else:
                        cross_arms[center].add(arm)

        modes = {}
        for cross, arms in cross_arms.items():
            arm_set = set(arms)

            # bar = the two horizontals or the two verticals
            if arm_set in ({"BR", "BL"}, {"TR", "TL"}):
                modes[cross] = "bar"

            # cross = diagonal
            elif arm_set in ({"TL", "BR"}, {"TR", "BL"}):
                modes[cross] = "cross"

            # split = any three out of four
            elif arm_set in ({"TR", "BR", "TL"}, {"TR", "BR", "BL"},
                             {"TL", "TR", "BL"}, {"TL", "BL", "BR"}):
                modes[cross] = "split"

            # arbitrary = all four arms
            elif arm_set == {"TL", "TR", "BR", "BL"}:
                modes[cross] = "arbitrary"

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
        p = Path(node1, node2, line_id)
        self.paths.append(p)
        return p    

    # def on_canvas_click(self, event):
    #     """Handles path selection."""
    #     for path in self.paths:
    #         coords = self.canvas.coords(path.line_id)
    #         if len(coords) >= 4 and self.is_point_near_line(event.x, event.y, *coords[:4], 15):  # 15 pixels tolerance
    #             self.toggle_path_selection(path)

    def on_canvas_click(self, event):
        """Handles clicks on non‐extension paths (cross‐arms) only."""
        # Use 10 px tolerance if grid_n is 12, else 15
        tolerance = 10 if self.grid_n == 12 else 15

        for path in self.paths:
            # Skip extension lines – they have tags like "input_label_X" or "output_label_X"
            tags = self.canvas.gettags(path.line_id)
            if any(t.startswith(("input_label_", "output_label_")) for t in tags):
                continue

            coords = self.canvas.coords(path.line_id)
            # Make sure we have at least two points (x1,y1,x2,y2)
            if len(coords) >= 4 and self.is_point_near_line(event.x, event.y, *coords[:4], tolerance):
                self.toggle_path_selection(path)



    def on_side_label_click(self, event, label_tag):
        """Clicking label now toggles both the text *and* its extension line."""
        # find all items (line + text) sharing this tag
        items = self.canvas.find_withtag(label_tag)
        if not items:
            return

        # decide new color
        current = self.canvas.itemcget(items[0], "fill")
        new_color = "white" if current=="red" else "red"

        # flip every item
        for item in items:
            self.canvas.itemconfig(item, fill=new_color)

        # now update AppData.selected_{input,output}_pins & self.selected_paths
        num = int(label_tag.split("_")[-1])
        if label_tag.startswith("input_label_"):
            AppData.selected_input_pins.clear()
            if new_color=="red":
                AppData.selected_input_pins.add(num)
        else:
            AppData.selected_output_pins.clear()
            if new_color=="red":
                AppData.selected_output_pins.add(num)

        # sync selected_paths for extension lines
        for path in self.paths:
            if label_tag in self.canvas.gettags(path.line_id):
                if new_color=="red":
                    self.selected_paths.add(path.line_id)
                else:
                    self.selected_paths.discard(path.line_id)
            
    # Multiple selection of output labels 
    def handle_input_label_selection(self, label_number):
        # Map label number to pin index
        pin_map = {
            "1": 1,
            "2": 2,
            "3": 3,
            "4": 4,
            "5": 5,
            "6": 6,
            "7": 7,
            "8": 8
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
            "1": 1,
            "2": 2,
            "3": 3,
            "4": 4,
            "5": 5,
            "6": 6,
            "7": 7,
            "8": 8
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
        adding = path.line_id not in self.selected_paths
        color  = "red" if adding else "white"

        # flip the line
        self.canvas.itemconfig(path.line_id, fill=color)
        if adding:
            self.selected_paths.add(path.line_id)
        else:
            self.selected_paths.remove(path.line_id)

        #— if the line has a side‐label tag, flip that text too
        for tag in self.canvas.gettags(path.line_id):
            if tag.startswith(("input_label_","output_label_")):
                for item in self.canvas.find_withtag(tag):
                    self.canvas.itemconfig(item, fill=color)

                # mirror pin state
                num = int(tag.split("_")[-1])
                if tag.startswith("input_label_"):
                    AppData.selected_input_pins.clear()
                    if adding:
                        AppData.selected_input_pins.add(num)
                else:
                    AppData.selected_output_pins.clear()
                    if adding:
                        AppData.selected_output_pins.add(num)
        
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
        elif mode == 'arbitrary':
            logging.info(f"{visible_label}: Arbitrary mode detected.")           
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
            theta_entry.insert(0, "0")
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

    def load_step(self, idx):
        """Import the JSON for step idx and refresh the grid selection."""
        json_str = self.step_lines[idx]
        self.import_paths_json(json_str)
        self.step_label.config(text=f"Step {self.current_step}/{len(self.step_lines)}") # update counter
        # self.import_calibration("calibration_steps.json")

    def prev_step(self):
        if not self.step_lines:
            return
        self.current_step = (self.current_step - 1) % len(self.step_lines)
        self.load_step(self.current_step)

    # def increment_step(self):
    #     """Increment the step counter by one and update the label."""
    #     # bump the counter
    #     self.current_step += 1

    #     # now update the button’s text
    #     self.step_label.configure(
    #         text=f"Step {self.current_step}/{len(self.step_lines)}"
    #     )

    def increment_step(self):
        """Go forward one step: load that step’s data from calibration_steps.json."""
        # 1) Load the file
        filepath = "calibration_steps.json"
        try:
            with open(filepath, "r") as f:
                payload = json.load(f)
        except Exception as e:
            logging.error("Could not open %s: %s", filepath, e)
            messagebox.showerror("Error", f"Cannot load calibration file:\n{e}")
            return

        steps = payload.get("steps", [])
        total = len(steps)
        if total == 0:
            messagebox.showwarning("No steps", "Calibration file has no steps.")
            return

        # 2) If we're already at the last step, do nothing
        if self.current_step >= total - 1:
            return

        # 3) Otherwise, load & render the next step
        self.import_calibration(step_idx=self.current_step + 1)


    # def increment_step(self):
    #     """
    #     Advance one step:
    #     - EDIT MODE: just bump through the steps you've saved (self.all_steps).
    #     - VIEW MODE: load the next step from calibration_steps.json.
    #     """
    #     if self.edit_mode:
    #         total = len(self.all_steps)
    #         # nothing to do if you haven't saved anything yet,
    #         # or if you're already on the last saved step
    #         if total == 0 or self.current_step >= total - 1:
    #             return

    #         # move to the next saved step
    #         self.current_step += 1

    #         # update the counter in 1-based form
    #         self.step_label.configure(
    #             text=f"Step {self.current_step+1}/{total}"
    #         )

    #     else:
    #         # VIEW MODE: import from merged JSON
    #         next_idx = self.current_step + 1
    #         self.import_calibration(step_idx=next_idx)

    # def decrement_step(self):
    #     """Decrement the step counter by one (down to 0) and update the label."""
    #     # don’t go below the first step
    #     if self.current_step <= 0:
    #         return

    #     # bump the counter down
    #     self.current_step -= 1

    #     # update the on-screen label
    #     self.step_label.configure(
    #         text=f"Step {self.current_step}/{len(self.step_lines)}"
    #     )

    def decrement_step(self):
        """Go back one step: load that step’s data from calibration_steps.json."""
        # If we're already at the first step, do nothing
        if self.current_step <= 0:
            return

        # Load & render step (this also updates self.current_step and the label)
        self.import_calibration(step_idx=self.current_step - 1)


    def save_current_and_next_step(self):
        """
        Save the current calibration step into the merged JSON file,
        then advance the counter and load the next step.
        """
        # 1) save the data for the current step
        try:
            self.save_current_step()
        except Exception as e:
            logging.error("Aborting advance: failed to save current step: %s", e)
            messagebox.showerror("Error", f"Could not save current step: {e}")
            return

        # 2) advance to the next step (and load it)
        self.increment_step()

    def toggle_play(self):
        if self.playing:
            # stop
            self.playing = False
            self.play_btn.configure(text="▶ Play")
        else:
            # start
            self.playing = True
            self.play_btn.configure(text="⏸ Pause")
            self._auto_advance()

    def _auto_advance(self):
        """Advance one step every 1 second while playing."""
        if not self.playing:
            return
        self.next_step()
        # schedule next advance in 1 000 ms
        self.after(600, self._auto_advance)

    def export_calibration_step(self):
        """
        Build a calibration‐step dict matching your JSON schema:
          {
            "step": 0,
            "input_port": 1,
            "output_port": 12,
            "calibration": "RP",
            "calibration_node": "A1",
            "Phase_shifter": "Internal",
            "Io_config": "Cross",
            "additional_nodes": { ... }
          }
        """
        # 1) Step index
        step = len(self.all_steps)
        logging.info(f"Exporting step {step}")


        # 2) Grab the one selected input/output pin (they are stored as ints 1–8)
        input_port  = next(iter(AppData.selected_input_pins),  None)
        output_port = next(iter(AppData.selected_output_pins), None)

        # 3) Calibration node = the one cross‐label stored in AppData.selected_label
        cal_node = AppData.selected_label if isinstance(AppData.selected_label, str) else None


        # 4) Phase shifter choice from AppData
        phase_shifter = AppData.phase_shifter_selection

        # 5) Compute Io_config + additional_nodes from the current cross modes
        cross_modes = self.get_cross_modes_numbers()  # e.g. {"A1":"cross", "B1":"bar", ...}
        # io_config = cross_modes.get(cal_node, "cross").capitalize()

       # if cal_node is None or missing, default to “Cross”
        io_config = (
            cross_modes.get(cal_node, "cross").capitalize()
            if cal_node in cross_modes
            else "Cross"
        )

        additional_nodes = {
            node: mode.capitalize()
            for node, mode in cross_modes.items()
            if node != cal_node
        }

        # 6) Assemble and return the dict
        return {
            "step":             step,
            "input_port":       input_port,
            "output_port":      output_port,
            "calibration":      "RP",
            "calibration_node": cal_node,
            "Phase_shifter":    phase_shifter,
            "Io_config":        io_config,
            "additional_nodes": additional_nodes
        }
    

    def save_current_step(self):
        """
        Called when the Save button is clicked:
          - builds the current calibration‐step dict
          - writes it to step_<n>.json
        """
        # 1) export current‐step dict
        step_data = self.export_calibration_step()

        # 2) append
        # self.all_steps.append(step_data)
        # 2) overwrite if editing an existing step, otherwise append
        if 0 <= self.current_step < len(self.all_steps):
            self.all_steps[self.current_step] = step_data
        else:
            self.all_steps.append(step_data)
            
        # 3) build top‐level structure
        payload = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "total_steps": len(self.all_steps),
                # you can add more global fields here, e.g.
                # "phase_shifter": AppData.phase_shifter_selection
            },
            "steps": self.all_steps
        }

        # 4) write single file
        try:
            with open("calibration_steps.json", "w") as f:
                json.dump(payload, f, indent=2)
                self.current_step += 1  # Advance the step counter after saving
                # logging.info(f"Saved: Merged {len(self.all_steps)} steps into calibration_steps.json")
        

        except Exception as e:
            logging.error("Failed to write merged JSON: %s", e)
            messagebox.showerror("Error", f"Could not save merged file: {e}")

    def next_step(self):
        """Just advance the counter & load without saving (view mode)."""
        self.current_step += 1
        AppData.current_calibration_step = self.current_step
        logging.info(f"Advancing to step {self.current_step}")
        self.import_calibration(step_idx=self.current_step)

    def toggle_edit_mode(self):
        """Toggle between view and edit modes."""
        # if we’re about to go into edit mode, load the master file
        if not self.edit_mode:
            # …you’re switching *into* edit mode…
            if os.path.exists("calibration_steps.json"):
                try:
                    with open("calibration_steps.json","r") as f:
                        payload = json.load(f)
                    self.all_steps = payload.get("steps", [])
                except Exception as e:
                    logging.warning("Could not pre-load existing steps: %s", e)
                    self.all_steps = []
        # now flip the flag
        self.edit_mode = not self.edit_mode

        if self.edit_mode:
            self.mode_btn.configure(text="✏️ Edit")
            self.next_btn.configure(command=self.save_current_and_next_step)
            for b in (self.back_btn, self.play_btn, self.next_btn):
                b.configure(fg_color="red", hover_color="#690000", text_color="black")
        else:
            self.mode_btn.configure(text="👁️ View")
            self.next_btn.configure(command=self.next_step)
            for b in (self.back_btn, self.play_btn, self.next_btn):
                b.configure(fg_color="transparent", hover_color="#144870", text_color="white")

    # def save_current_step(self):
    #     """
    #     Called when the Save button is clicked:
    #       - builds the current calibration‐step dict
    #       - writes it to step_<n>.json
    #     """
    #     # 1) export current‐step dict
    #     step_data = self.export_calibration_step()

    #     # 2) append
    #     self.all_steps.append(step_data)

    #     # 3) build top‐level structure
    #     payload = {
    #         "metadata": {
    #             "created_at": datetime.now().isoformat(),
    #             "total_steps": len(self.all_steps),
    #             # you can add more global fields here, e.g.
    #             # "phase_shifter": AppData.phase_shifter_selection
    #         },
    #         "steps": self.all_steps
    #     }

    #     # 4) write single file
    #     try:
    #         with open("calibration_steps.json", "w") as f:
    #             json.dump(payload, f, indent=2)
    #             # logging.info(f"Saved: Merged {len(self.all_steps)} steps into calibration_steps.json")

    #     except Exception as e:
    #         logging.error("Failed to write merged JSON: %s", e)
    #         messagebox.showerror("Error", f"Could not save merged file: {e}")

    # def next_step(self):
    #     """Just advance the counter & load without saving (view mode)."""
    #     self.current_step += 1
    #     logging.info(f"Advancing to step {self.current_step}")
    #     self.import_calibration(step_idx=self.current_step)

    # def toggle_edit_mode(self):
    #     """Toggle between view and edit modes.
    #        In edit mode, Next ⏭ will SAVE instead of advancing."""
    #     self.edit_mode = not self.edit_mode

    #     if self.edit_mode:
    #         # now in edit mode
    #         self.mode_btn.configure(text="✏️ Edit")
    #         # Next → save
    #         self.next_btn.configure(command=self.save_current_and_next_step)
    #         # visually highlight “Next” when it’s acting as save
    #         for b in (self.back_btn, self.play_btn, self.next_btn):
    #             b.configure(fg_color="red", hover_color="#690000", text_color="black")
    #         self.next_btn.configure(command=self.save_current_and_next_step)

    #     else:
    #         # back to view mode
    #         self.mode_btn.configure(text="👁️ View")
    #         # Next → just advance
    #         self.next_btn.configure(command=self.next_step)
    #         # restore default look
    #         for b in (self.back_btn, self.play_btn, self.next_btn):
    #            b.configure(fg_color="transparent", hover_color = "#144870", text_color="white")
    #         self.next_btn.configure(command=self.next_step)


    def import_calibration(self, filepath="calibration_steps.json", step_idx=None):
        """
        Load calibration_steps.json, pick out step #step_idx (0-based),
        highlight:
        - Cross‐center labels (orange + green) and arms (red)
        - Input/output side‐labels and extension lines (red)
        """
        # 1) Load JSON
        try:
            with open(filepath, "r") as f:
                payload = json.load(f)
        except Exception as e:
            logging.error("Failed to load %s: %s", filepath, e)
            messagebox.showerror("Error", f"Could not load calibration file:\n{e}")
            return

        steps = payload.get("steps", [])
        total = len(steps)
        if total == 0:
            messagebox.showwarning("No steps", "Calibration file has no steps.")
            return

        # 2) Clamp step index
        idx = 0 if step_idx is None else max(0, min(step_idx, total - 1))
        step_data = steps[idx]

        # 3) Clear all old highlights
        #    a) Lines
        for p in self.paths:
            self.canvas.itemconfig(p.line_id, fill="white")
        self.selected_paths.clear()

        #    b) Cross‐labels
        for tid in self.cross_labels.values():
            self.canvas.itemconfig(tid, fill="white")

        #    c) IO labels (common tag "io_label")
        self.canvas.itemconfig("io_label", fill="white")
        AppData.selected_input_pins.clear()
        AppData.selected_output_pins.clear()

        # 4) Highlight cross‐centers and arms (as before) …
        arm_specs = {}
        # 4a) calibration_node
        cal_label = step_data.get("calibration_node")
        io_mode   = step_data.get("Io_config", "")
        if cal_label:
            arm_specs[cal_label] = mode_to_arms(io_mode)
            # text label → orange
            for key, tid in self.cross_labels.items():
                if self.canvas.itemcget(tid, "text") == cal_label:
                    self.canvas.itemconfig(tid, fill="orange")
                    break
        # 4b) additional_nodes → green
        for node_label, mode_str in step_data.get("additional_nodes", {}).items():
            arm_specs[node_label] = mode_to_arms(mode_str)
            for key, tid in self.cross_labels.items():
                if self.canvas.itemcget(tid, "text") == node_label:
                    self.canvas.itemconfig(tid, fill="white")
                    break
        # 4c) color those arms red
        for path in self.paths:
            center, arm = self._parse_path_components(path)
            if center in arm_specs and arm in arm_specs[center]:
                self.canvas.itemconfig(path.line_id, fill="red")
                self.selected_paths.add(path.line_id)

        # 5) Highlight input_port / output_port
        inp = step_data.get("input_port")
        outp = step_data.get("output_port")

        def _highlight_io(port, tag_prefix, pin_set):
            if port is None:
                return
            lbl_tag = f"{tag_prefix}_label_{port}"
            # 5a) highlight the text
            self.canvas.itemconfig(lbl_tag, fill="red")
            pin_set.clear()
            pin_set.add(port)
            # 5b) highlight its extension line(s)
            for path in self.paths:
                if lbl_tag in self.canvas.gettags(path.line_id):
                    self.canvas.itemconfig(path.line_id, fill="red")
                    self.selected_paths.add(path.line_id)

        _highlight_io(inp,  "input",  AppData.selected_input_pins)
        _highlight_io(outp, "output", AppData.selected_output_pins)

        # 6) Re-create any needed input‐boxes (θ/φ) for crosses
        for center_label, arms in arm_specs.items():
            if arms and center_label not in self.input_boxes:
                self.create_input_boxes(center_label)

        # 7) Update counter & state
        self.current_step = idx
        self.step_label.configure(text=f"Step {idx}/{total}")

        # 8) Fire update event
        self.event_generate("<<SelectionUpdated>>")
        self.update_selection()

    def increment_step(self):
        """
        Advance one step:
          • In edit mode: always bump the counter so you can add new steps
          • In view mode: load the next step from calibration_steps.json
        """
        if self.edit_mode:
            # — EDIT mode: just advance the counter, no clamping —
            self.current_step += 1
            total = len(self.all_steps)
            # if you prefer 1-based display, do current_step+1 here
            self.step_label.configure(text=f"Step {self.current_step}/{total}")
            return

        # — VIEW mode: pull from calibration_steps.json —
        # note: import_calibration will clamp internally if you go past the end
        self.import_calibration(step_idx=self.current_step + 1)

    # def increment_step(self):
    #     """
    #     Advance one step:
    #       • In edit mode: just move through self.all_steps.
    #       • In view mode: load the next step from calibration_steps.json.
    #     """
    #     if self.edit_mode:
    #         # — EDIT mode: walk through the saved steps list —
    #         total = len(self.all_steps)
    #         if total == 0:
    #             return  # nothing to do
    #         # clamp and advance
    #         next_idx = min(self.current_step + 1, total - 1)
    #         if next_idx != self.current_step:
    #             self.current_step = next_idx
    #             # refresh label, 1-based
    #             self.step_label.configure(text=f"Step {self.current_step}/{total}")

    #     else:
    #         # — VIEW mode: pull from the merged JSON file —
    #         # ask import_calibration to load step current_step+1
    #         self.import_calibration(step_idx=self.current_step)

    # def import_calibration(self, filepath="calibration_steps.json", step_idx=None):
    #     """
    #     Load merged calibration JSON and highlight nodes for one step.
    #     If step_idx is None, it tries to match JSON 'step' == self.current_step,
    #     otherwise falls back to the first step.
    #     """
    #     try:
    #         with open(filepath, "r") as f:
    #             payload = json.load(f)
    #     except Exception as e:
    #         logging.error("Failed to load calibration file: %s", e)
    #         messagebox.showerror("Error", f"Could not load calibration file:\n{e}")
    #         return

    #     steps = payload.get("steps", [])
    #     if not steps:
    #         messagebox.showwarning("No steps", "That file contains no steps.")
    #         return

    #     # pick the right step
    #     if step_idx is None:
    #         step_data = next((s for s in steps if s.get("step") == self.current_step), steps[0])
    #         idx = step_data.get("step", 0)
    #     else:
    #         if not (0 <= step_idx < len(steps)):
    #             messagebox.showwarning(
    #                 "Invalid step",
    #                 f"Step index {step_idx} out of range (0–{len(steps)-1})."
    #             )
    #             return
    #         step_data = steps[step_idx]
    #         idx = step_idx

    #     # highlight it
    #     self._highlight_step(step_data)

    #     # update the UI counter: show “Step X/Y”
    #     total = len(steps)
    #     self.step_label.configure(text=f"Step {idx}/{total-1}")
    #     # keep self.current_step in sync
    #     self.current_step = idx

    def _highlight_step(self, step_data):
        """
        Given one step dict, clear old highlights and
        highlight calibration_node + additional_nodes.
        """
        cal_node = step_data.get("calibration_node")
        additional = step_data.get("additional_nodes", {})

        # clear existing highlights (text items back to white)
        for text_id in self.cross_labels.values():
            self.canvas.itemconfig(text_id, fill="white")

        # highlight main calibration node in orange
        if cal_node:
            # find internal key for cal_node label
            for key, text_id in self.cross_labels.items():
                if self.canvas.itemcget(text_id, 'text') == cal_node:
                    self.canvas.itemconfig(text_id, fill="orange")
                    break

        # highlight additional nodes (green for Cross, red otherwise)
        for node_name, mode in additional.items():
            for key, text_id in self.cross_labels.items():
                if self.canvas.itemcget(text_id, 'text') == node_name:
                    color = 'white' if mode.lower() == 'cross' else 'red'
                    self.canvas.itemconfig(text_id, fill=color)
                    break

        # update counter display
        self.step_label.configure(text=f"Step {step_data.get('step', self.current_step)}/{len(self.step_lines)}")



    def convert_calibration_to_grid_inline(calibration_json, get_cross_modes_func):
        """
        Convert calibration JSON to inline JSON strings per step.
        Each step is output as a single-line JSON of nodes.
        """
        lines = []
        cross_modes = get_cross_modes_func()

        for step_data in calibration_json.get("calibration_steps", []):
            grid = {}

            # Calibration node
            cal_node = step_data["calibration_node"]
            mode = step_data.get("Io_config", cross_modes.get(cal_node, "cross"))
            grid[cal_node] = {"arms": mode_to_arms(mode), "theta": "0", "phi": "0"}

            # Additional nodes
            for node, io_state in step_data.get("additional_nodes", {}).items():
                grid[node] = {"arms": mode_to_arms(io_state.lower()), "theta": "0", "phi": "0"}

            # Dump as single-line JSON
            line = json.dumps(grid, separators=(',', ':'))
            lines.append(line)

        return lines

    def _on_play_clicked(self):
        """
        When ▶ Play is clicked:
          • if an auto_calibrate_callback was provided → call it.
          • else → fall back to the old toggle_play behavior.
        """
        # if callable(self.auto_calibrate_callback):
        #     # hand off control to window1.auto_calibrate()
        #     self.auto_calibrate_callback()
        # else:
        #     # no callback set → just do the regular play/step
        #     self.toggle_play()
        # 1) always flip the play/pause state and button text
        self.toggle_play()

        # 2) if we just went into PLAY, hand off to the window’s auto_calibrate
        if self.playing and callable(self.auto_calibrate_callback):
            self.auto_calibrate_callback()


    def get_cross_modes_numbers(self):
        """
        Returns a dict mapping each cross label to one of:
        - "bar0"/"bar1" (two‐arm horizontal/vertical)
        - "cross0"/"cross1" (two‐arm diagonals)
        - "split0"…"split3" (three‐arm patterns, missing TL, TR, BR, or BL)
        - "arbitrary" (all four arms)
        """
        cross_arms = defaultdict(set)
        for path in self.paths:
            if path.line_id in self.selected_paths:
                center, arm = self._parse_path_components(path)
                if center and arm:
                    # If arm is a compound like "TL-BR", split it
                    for a in arm.split("-"):
                        cross_arms[center].add(a)

        modes = {}
        for cross, arms in cross_arms.items():
            arm_set = set(arms)
            # BAR patterns
            if   arm_set == {"TL", "TR"}:
                modes[cross] = "bar0"
            elif arm_set == {"BL", "BR"}:
                modes[cross] = "bar1"

            # CROSS patterns
            elif arm_set == {"TL", "BR"}:
                modes[cross] = "cross0"
            elif arm_set == {"TR", "BL"}:
                modes[cross] = "cross1"

            # SPLIT patterns: one missing arm
            elif len(arm_set) == 3:
                # Determine which arm is missing
                all_arms = {"TL", "TR", "BR", "BL"}
                missing = (all_arms - arm_set).pop()  # get the one missing
                missing_index = {"TL": 0, "TR": 1, "BR": 2, "BL": 3}[missing]
                modes[cross] = f"split{missing_index}"

            # ARBITRARY: all four arms
            elif arm_set == {"TL", "TR", "BR", "BL"}:
                modes[cross] = "arbitrary"

        return modes


def mode_to_arms(mode):
    """
    Convert IO mode (with 0–3 suffix) to the list of arms.
    """
    m = mode.lower()
    # BAR patterns
    if m == "bar0":
        return ["TL", "TR"]
    if m == "bar1":
        return ["BL", "BR"]

    # CROSS patterns
    if m == "cross0":
        return ["TL", "BR"]
    if m == "cross1":
        return ["TR", "BL"]

    # SPLIT patterns (3-of-4); split means missing arm index N
    if m == "split0":  # missing TL
        return ["TR", "BR", "BL"]
    if m == "split1":  # missing TR
        return ["TL", "BR", "BL"]
    if m == "split2":  # missing BR
        return ["TL", "TR", "BL"]
    if m == "split3":  # missing BL
        return ["TL", "TR", "BR"]

    # ARBITRARY: all four arms
    if m == "arbitrary":
        return ["TL", "TR", "BL", "BR"]

    # fallback: no arms
    return []





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