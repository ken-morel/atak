"""Atak application definition."""
import pyoload

from . import pyodchecks
from .pagebrowser import PageBrowser
from importlib import import_module
from typing import Callable


class AtakApplication:
    """Atak base application class."""

    def __init__(self):
        """Initialize atak application."""
        self.pagebrowser = PageBrowser()


@pyoload(validators=dict(path=pyodchecks.path))
def get_cmd(path: str) -> Callable:
    """Get the function pointed by url."""
    mod, fn = path.split(":")
    return getattr(import_module(mod), fn)


@pyoload
class AppExit(Exception):
    """Exit of application."""

    code: int

    def __init__(self, code: int):
        """Exit with the given exit code."""
        super(AppExit, self).__init__()
        self.code = code
