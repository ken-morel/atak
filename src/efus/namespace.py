"""Holds the namespace class, responsible for efus component namespaces."""


import functools
import importlib
import typing

from . import constants
from . import subscribe
from . import types
from pyoload import *

# from .parser import types


class Namespace(dict, subscribe.Subscribeable):
    """Component namespace."""

    dirty: bool
    parents: "tuple[Namespace]"

    @classmethod
    @functools.cache
    def defaults(cls):
        """Get default and basic namespace variables provided by efus."""
        return {k: v for k, v in vars(constants).items() if not k[0] == "_"}

    def __init__(self, parents: "tuple[Namespace]" = (), default: dict = {}):
        """Initialize with default value."""
        self.dirty = False
        self.parents = parents
        dict.__init__(self, Namespace.defaults())
        dict.update(self, default)
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

    def get_name(self, name: str) -> typing.Any:
        """
        Return name or raise error.

        :raises NameError: If name not found
        """
        if (val := self.get(name)) is not types.ENil:
            return val
        else:
            raise NameError(f"Name: {name} not in namespace {self!r}.")

    def get(
        self, name: str, head: "typing.Optional[Namespace]" = None
    ) -> typing.Any:
        """Search for `name` in self and parent namespaces."""
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

    @annotate
    def import_module(
        self,
        module: str,
        names=typing.Union[typing.Literal["all"], tuple[str]],
    ):
        mod = importlib.import_module(module)
        if names == "all":
            if hasattr(mod, "__all__"):
                names = mod.__all__
            else:
                names = [x for x in dir(mod) if not x[0] == "_"]
        assert isinstance(
            names, typing.Iterable
        ), "names param should be iterable or None"
        for name in names:
            self[name] = getattr(mod, name)
