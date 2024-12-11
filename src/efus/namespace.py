"""Holds the namespace class, responsible for efus component namespaces."""


from . import subscribe
from . import types
import typing

# from .parser import types


class Namespace(dict, subscribe.Subscribeable):
    """Component namespace."""

    dirty: bool
    parents: "tuple[Namespace]"

    def __init__(self, parents: "tuple[Namespace]" = (), default: dict = {}):
        """Initialize with default value."""
        self.dirty = False
        self.parents = parents
        dict.__init__(self, default)
        subscribe.Subscribeable.__init__(self)

    def __setitem__(self, item: str, value: typing.Any):
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

    def name(self, name: str) -> typing.Any:
        """
        Return name or raise error

        :raises NameError: If name not found
        """
        if (val := self.get(name)) is not types.ENil:
            return val
        else:
            raise NameError(f"Name: {name} not in namespace {self!r}.")

    def get(
        self, name: str, head: "typing.Optional[Namespace]" = None
    ) -> typing.Any:
        if name in self:
            return self[name]
        else:
            for parent in self.parents:
                if parent is head:
                    raise RecursionError(f"Circular namespace parents.")
                if (v := parent.get(name, head)) is not types.ENil:
                    return v
            else:
                return types.ENil
