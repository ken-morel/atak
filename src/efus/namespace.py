"""Holds the namespace class, responsible for efus component namespaces."""


from .subscribe import Subscribeable
from typing import Any
from .types import EObject


class Namespace(dict, Subscribeable, EObject):
    """Component namespace."""

    dirty: bool

    def __init__(self, default: dict = {}):
        """Initialize with default value."""
        self.dirty = False
        dict.__init__(self, default)
        Subscribeable.__init__(self)

    def __setitem__(self, item: str, value: Any):
        self.dirty = True
        super().__setitem__(item, value)

    def update(self) -> bool:
        """
        Check if namespace is modified and warn subscribers.

        :returns: If subscribers were actually warned.
        """
        if self.dirty:
            self.warn_subscribers()
            self.dirty = False
            return True
        return False
