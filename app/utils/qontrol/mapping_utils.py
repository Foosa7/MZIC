from app.utils.appdata import AppData

def get_mapping_functions(grid_size=None):
    """
    Return the correct mapping functions for the given grid size.
    If no grid_size is provided, uses the size from AppData.
    
    Args:
        grid_size (str, optional): Grid size in format "NxN". If None, uses AppData.grid_size
        
    Returns:
        tuple: (create_label_mapping, apply_grid_mapping) functions
    """
    # If no grid_size provided, get from AppData
    if grid_size is None:
        if hasattr(AppData, 'grid_size'):
            grid_size = AppData.grid_size
        else:
            # Default to 8x8 if not set
            grid_size = "8x8"
    
    n = int(str(grid_size).split('x')[0])
    if n == 12:
        from app.utils.qontrol import qmapper12x12
        return qmapper12x12.create_label_mapping, qmapper12x12.apply_grid_mapping
    else:
        from app.utils.qontrol import qmapper8x8
        return qmapper8x8.create_label_mapping, qmapper8x8.apply_grid_mapping