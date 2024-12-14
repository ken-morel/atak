"""\
Provide basic functions to most used taktk functions and components
Copyright (C) 2022  ken-morel

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from typing import Any, Callable, Optional

from pyoload import annotate

_app = None


class NilType:
    """
    Simple type to describe inexistence of value, used in components
    some other parts of taktk
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "Nil"

    def __reduce__(self):
        return (self.__class__, ())

    def __bool__(self):
        return False

    def __instancecheck__(self, other: Any):
        return other is Nil

    def __sub__(self, other: Any):
        return other is Nil

    def __rsub__(self, other: Any):
        return other is Nil


Nil = NilType()


@annotate
def resolve(value: Any, callback: Optional[Callable] = None) -> Any:
    """
    basicly resolves from taktk descriptors as Media or Writeable
    to the underlying value. if it is not a media resource or
    writeable, the value is returned
    """
    from .media import Resource
    from .writeable import Writeable

    if isinstance(value, Resource | Writeable):
        if isinstance(value, Writeable) and callback is not None:
            value.subscribe(callback)
        return value.get()
    else:
        return value


ON_CREATE_HANDLERS: set[Callable] = set()


def on_create(func: Callable) -> Callable:
    """
    Registers the function to be called after the window initialization.
    The function is added to `taktk.ON_CREATE_HANDLERS` set

    :returns: The passed callable
    """
    ON_CREATE_HANDLERS.add(func)
    if _app is not None:
        func(_app)
    return func


def get_app():
    return _app


def notify(*args, **kw):
    from . import notification

    notification.Notification(*args, **kw).show()


def make_menu(*args, **kw):
    from . import menu

    return menu.Menu(*args, **kw)


__version__ = "0.1.0a1"
__author__ = "ken-morel"
__all__ = ["Nil", "on_create", "notify"]
