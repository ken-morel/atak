#### From ttkbootstrap.utility


def scale_size(widget, size):
    """Scale the size based on the scaling factor of tkinter.
    This is used most frequently to adjust the assets for
    image-based widget layouts and font sizes.

    Parameters:

        widget (Widget):
            The widget object.

        size (Union[int, List, Tuple]):
            A single integer or an iterable of integers

    Returns:

        Union[int, List]:
            An integer or list of integers representing the new size.
    """
    BASELINE = 1.33398982438864281
    scaling = widget.tk.call("tk", "scaling")
    factor = scaling / BASELINE

    if isinstance(size, int):
        return int(size * factor)
    elif isinstance(size, tuple) or isinstance(size, list):
        return [int(x * factor) for x in size]
