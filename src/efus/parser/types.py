"""Efus base and complex types."""
from abc import ABC
from ..subscribe import Subscribeable
from typing import Any, Optional
from decimal import Decimal
from dataclasses import dataclass

Namespace = None  # TODO: remove this


class EObject(ABC, Subscribeable):
    """Efus base object value class."""

    value: Any

    def __init__(self, value: Any):
        """Initialize default for EObject Subsclasses."""
        self.value = value

    def eval(self):
        """Evaluate to a python object."""
        raise NotImplementedError(
            f"Cannot convert object of type {self.__class__.__name__} "
            + "to python ewuivalent."
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value!r})"


def _py_eval(self) -> Any:
    """Return underlying value."""
    return self.value


def _py_evals(cls):
    cls.eval = _py_eval
    return cls


class ENumber(EObject):
    """Efus Number object."""

    value: int | Decimal


class EStr(EObject):
    """Efus Integer object."""

    value: str

    def eval(self, namespace: Namespace):
        return self.value % namespace


class EInstr(EObject):
    """ "Efus instruction base."""

    pass


@dataclass
class TagDef(EInstr):
    """Tag definition"""

    name: str
    alias: Optional[str]
    attributes: dict


class Efus(EObject):
    """Efus source code base."""

    instructions: tuple[EInstr]

    def __init__(self, instrs: tuple[EInstr]):
        self.instructions = instrs

    def __repr__(self):
        return str(tuple(self.instructions))
