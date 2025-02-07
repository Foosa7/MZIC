#!/usr/bin/python
from tkinter import Tk, Canvas, Frame, BOTH, Label

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
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.master.title("Selectable X-Shaped Pathways")
        self.pack(fill=BOTH, expand=1)
        
        # Create a label to display coordinates
        self.coord_label = Label(self, text="X: 0, Y: 0", font=("Arial", 12))
        self.coord_label.pack(anchor='nw')  # Place the label at the top-left corner
        
        self.canvas = Canvas(self)
        self.nodes = {}  # Stores nodes by name
        self.paths = []  # Stores all paths
        self.selected_paths = set()  # Tracks selected paths
        
        # Create X shape with center at (275,275) and initial side lengths

        # Arrangement for 4x4 setting

        # Create X shape with center at (275,275) and initial side lengths
        # self.create_x_shape("A1", 50, 50, tl_length=50, tr_length=50, bl_length=50, br_length=50)
        # self.create_x_shape("A2", 50, 50+200, tl_length=50, tr_length=50, bl_length=50, br_length=50)
        # self.create_x_shape("B1", 150, 150, tl_length=50, tr_length=50, bl_length=50, br_length=50)
        # self.create_x_shape("C1", 150+100,50, tl_length=50, tr_length=50, bl_length=50, br_length=50)
        # self.create_x_shape("C2", 150+100,50+200, tl_length=50, tr_length=50, bl_length=50, br_length=50)

        # Arrangement for 6x6 setting

        self.create_x_shape("A1", 50, 50, tl_length=50, tr_length=50, bl_length=50, br_length=50)
        self.create_x_shape("A2", 50, 50+200, tl_length=50, tr_length=50, bl_length=50, br_length=50)
        self.create_x_shape("A3", 50, 50+200*2, tl_length=50, tr_length=50, bl_length=50, br_length=50)
        self.create_x_shape("B1", 150, 150, tl_length=50, tr_length=50, bl_length=50, br_length=50)
        self.create_x_shape("B2", 150, 150+200, tl_length=50, tr_length=50, bl_length=50, br_length=50)
        self.create_x_shape("C1", 150+100,50, tl_length=50, tr_length=50, bl_length=50, br_length=50)
        self.create_x_shape("C2", 150+100,50+200, tl_length=50, tr_length=50, bl_length=50, br_length=50)
        self.create_x_shape("C3", 150+100,50+200*2, tl_length=50, tr_length=50, bl_length=50, br_length=50)
        self.create_x_shape("D1", 150+200, 150, tl_length=50, tr_length=50, bl_length=50, br_length=50)
        self.create_x_shape("D2", 150+200, 150+200, tl_length=50, tr_length=50, bl_length=50, br_length=50)
        self.create_x_shape("C1", 150+100+200,50, tl_length=50, tr_length=50, bl_length=50, br_length=50)
        self.create_x_shape("C2", 150+100+200,50+200, tl_length=50, tr_length=50, bl_length=50, br_length=50)
        self.create_x_shape("C3", 150+100+200,50+200*2, tl_length=50, tr_length=50, bl_length=50, br_length=50)
        self.create_x_shape("F1", 150+200+200, 150, tl_length=50, tr_length=50, bl_length=50, br_length=50)
        self.create_x_shape("F2", 150+200+200, 150+200, tl_length=50, tr_length=50, bl_length=50, br_length=50)        


        # Bind mouse motion to update coordinates
        self.canvas.bind("<Motion>", self.show_coordinates)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.pack(fill=BOTH, expand=1)

    def create_x_shape(self, center_name, x, y, tl_length=50, tr_length=50, bl_length=50, br_length=50):
        """
        Creates an X shape with a center node and four diagonal paths.
        Each arm of the X can have a different length.
        """
        # Create center node
        self.nodes[center_name] = Node(center_name, x, y)
        
        # Directions for peripheral nodes (relative to center)
        directions = {
            "TL": (-tl_length, -tl_length),  # Top-left
            "TR": (tr_length, -tr_length),   # Top-right
            "BL": (-bl_length, bl_length),   # Bottom-left
            "BR": (br_length, br_length)     # Bottom-right
        }
        
        # Create peripheral nodes and connect them to the center
        for suffix, (dx, dy) in directions.items():
            node_name = f"{center_name}_{suffix}"
            self.nodes[node_name] = Node(node_name, x + dx, y + dy)
            self.create_path(self.nodes[center_name], self.nodes[node_name])

    def update_x_shape(self, center_name, new_x, new_y, tr_length, tl_length, br_length, bl_length):
        """Updates the X shape's position and side lengths."""
        center = self.nodes.get(center_name)
        if not center:
            print(f"Error: Center node '{center_name}' not found.")
            return
        
        # Update center position
        center.x, center.y = new_x, new_y
        
        # Directions for peripheral nodes
        directions = {
            "TL": (-tl_length, -tl_length),
            "TR": (tr_length, -tr_length),
            "BL": (-bl_length, bl_length),
            "BR": (br_length, br_length)
        }
        
        # Update peripheral nodes and paths
        for suffix, (dx, dy) in directions.items():
            node_name = f"{center_name}_{suffix}"
            node = self.nodes.get(node_name)
            if node:
                node.x = new_x + dx
                node.y = new_y + dy
            else:
                print(f"Error: Peripheral node '{node_name}' not found.")
        
        # Update all paths connected to the center
        for path in self.paths:
            if path.node1.name == center_name or path.node2.name == center_name:
                self.canvas.coords(
                    path.line_id,
                    path.node1.x, path.node1.y,
                    path.node2.x, path.node2.y
                )

    def create_path(self, node1, node2):
        """Creates a visual path between two nodes."""
        line_id = self.canvas.create_line(
            node1.x, node1.y,
            node2.x, node2.y,
            fill="blue", width=2
        )
        self.paths.append(Path(node1, node2, line_id))

    def on_canvas_click(self, event):
        """Handles path selection/deselection on click."""
        for path in self.paths:
            coords = self.canvas.coords(path.line_id)
            x1, y1, x2, y2 = coords
            if self.is_point_near_line(event.x, event.y, x1, y1, x2, y2, 8):
                if path.line_id in self.selected_paths:
                    self.canvas.itemconfig(path.line_id, fill="blue")
                    self.selected_paths.remove(path.line_id)
                    print(f"Deselected path: {path.node1.name} -> {path.node2.name}")
                else:
                    self.canvas.itemconfig(path.line_id, fill="red")
                    self.selected_paths.add(path.line_id)
                    print(f"Selected path: {path.node1.name} -> {path.node2.name}")
                return

    def is_point_near_line(self, px, py, x1, y1, x2, y2, threshold):
        """Checks if a point is near a line segment."""
        dx = x2 - x1
        dy = y2 - y1
        pdx = px - x1
        pdy = py - y1
        t = (pdx * dx + pdy * dy) / (dx**2 + dy**2) if (dx != 0 or dy != 0) else 0
        t = max(0, min(1, t))
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        distance = ((px - closest_x)**2 + (py - closest_y)**2)**0.5
        return distance <= threshold

    def show_coordinates(self, event):
        """Updates the label with the current mouse coordinates."""
        self.coord_label.config(text=f"X: {event.x}, Y: {event.y}")

def main():
    root = Tk()
    ex = Example()
    root.geometry("1000x1000")
    root.mainloop()

if __name__ == '__main__':
    main()