"""Pyoload debug checker functions."""


def path(path: str):
    """Check if is a valid command path."""
    if (c := path.count(":")) != 1:
        return (
            f"Path should include one ':' (not {c}), {path!r}\n"
            + "(should be in format 'module:function')"
        )
