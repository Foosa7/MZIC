def get_mapping_functions(grid_size):
    """
    Return the correct mapping functions for the given grid size.
    Usage:
        create_label_mapping, apply_grid_mapping = get_mapping_functions(grid_size)
    """
    n = int(str(grid_size).split('x')[0])
    if n == 12:
        from app.utils.qontrol import qmapper12x12
        return qmapper12x12.create_label_mapping, qmapper12x12.apply_grid_mapping
    else:
        from app.utils.qontrol import qmapper8x8
        return qmapper8x8.create_label_mapping, qmapper8x8.apply_grid_mapping