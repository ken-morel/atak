"""Efus base and complex types."""
from abc import ABC
from . import subscribe, namespace, component
from typing import Any, Optional
from decimal import Decimal
import dataclasses


class EObject(ABC, subscribe.Subscribeable):
    """Efus base object value class."""

    value: Any

    def __init__(self, value: Any):
        """Initialize default for EObject Subsclasses."""
        self.value = value

    def eval(self, namespace: namespace.Namespace):
        """Evaluate to a python object."""
        raise NotImplementedError(
            f"Cannot convert object of type {self.__class__.__name__} "
            + "to python ewuivalent."
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value!r})"


class ENilType(EObject):
    val = None

    def __new__(cls):
        if cls.val is None:
            cls.val = super().__new__(cls)
        return cls.val

    def __init__(self):
        pass

    def __bool__(self) -> bool:
        return False

    def __hash__(self):
        return 1

    @classmethod
    def eval(cls, namespace: namespace.Namespace) -> "ENilType":
        return cls()


ENil = ENilType()


class ENumber(EObject):
    """Efus Number object."""

    value: int | Decimal

    def eval(self, namespace: "namespace.Namespace"):
        return self.value


class EStr(EObject):
    """Efus Integer object."""

    value: str

    def eval(self, namespace: "namespace.Namespace"):
        return self.value % namespace


class EInstr(EObject):
    """ "Efus instruction base."""

    children: "list[EInstr]"

    def add_child(self, child: "EInstr"):
        self.children.append(child)

    def eval(
        self,
        parent_component: Optional[component.Component],
        namespace: namespace.Namespace,
    ) -> component.Component:
        child_component = self._eval(parent_component, namespace)
        for child_instruction in self.children:
            self.add_child_component(child_component)

    def _eval(
        self,
        namespace: namespace.Namespace,
        parent: Optional[component.Component] = None,
    ):
        pass


@dataclasses.dataclass
class TagDef(EInstr):
    """Tag definition"""

    name: str
    alias: Optional[str]
    attributes: dict
    children: list[EInstr] = dataclasses.field(default_factory=list)


class Efus(EObject):
    """Efus source code base."""

    parent_instruction: EInstr

    def __init__(self, parent_instruction: EInstr):
        self.parent_instruction = parent_instruction

    def __repr__(self):
        return str(self.parent_instruction)

    def translate(self, namespace: namespace.Namespace):
        """EValuate the code in the given namespace."""
        return self.parent_instruction.eval(namespace)

    eval = translate


class EScalar(EObject):
    """Efus variable scalar multiple."""

    coefficient: int | Decimal
    multiple: str

    def __init__(self, coefficient: int | Decimal, multiple: str):
        super().__init__()
        self.coefficient = coefficient
        self.multiple = multiple

    def eval(self, namespace: namespace.Namespace):
        """Return the scalar product of multiple and coefficient."""
        return self.coefficient * namespace.name(self.multiple)
