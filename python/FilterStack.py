from collections import deque

class Filters:
    """A simple stack-based undo/redo system for image filters."""
    index = -1
    modes = None
    filters = deque(maxlen=20)
    temp_filters = deque(maxlen=1)

    def __init__(self):
        pass

    def push(self, filter_data: dict):
        """`Push` new filters to the stack."""

        if not filter_data:
            return
            # raise ValueError(f"Filter data is {filter_data}, length is { len(Filters.temp_filters) }")  # or raise an error

        if Filters.modes == "cached":

            Filters.temp_filters.clear()
            Filters.temp_filters.append(filter_data)
            
        elif Filters.modes == "preview":
            
            while len(Filters.filters) - 1 > Filters.index:
                Filters.filters.pop()

            # Merge temp_filters into main stack
            Filters.filters.extend(Filters.temp_filters)
            Filters.filters.append(filter_data)
            Filters.temp_filters.clear()
            Filters.index = len(Filters.filters) - 1

    def undo(self):
        """ Classic `undo` feature that returns the current filter. """
        if not Filters.filters:
            return None
    
        if Filters.index > 0:
            Filters.index -= 1
            return Filters.filters[Filters.index]
        else:
            return None

    def redo(self):
        """ Classic `redo` feature that returns the current filter. """
        if not Filters.filters:
            return None
        
        if Filters.index < len(Filters.filters) - 1:
            Filters.index += 1
            return Filters.filters[Filters.index]
        else:
            return None
    
    def reset(self):
        """ Classic `reset` feature that clears the filter stack. """
        Filters.filters.clear()
        Filters.temp_filters.clear()
        Filters.index = -1