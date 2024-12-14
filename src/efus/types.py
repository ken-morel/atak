"""Efus base and complex types."""
import dataclasses

import typing

from . import component
from . import namespace
from . import subscribe
from abc import ABC
from pyoload import *


class EObject(ABC, subscribe.Subscribeable):
    """Efus base object value class."""

    value: typing.Any = None

    def __init__(self, value: typing.Any = None):
        """Initialize default for EObject Subsclasses."""
        self.value = value

    @annotate
    def eval(self, namespace: "namespace.Namespace"):
        """Evaluate to a python object."""
        raise NotImplementedError(
            f"Cannot convert object of type {self.__class__.__name__} "
            + "to python ewuivalent."
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value!r})"


class ENilType(EObject):
    """Efus ENil type."""

    val = None

    def __new__(cls):
        """Return or create the singleton ENil."""
        if cls.val is None:
            cls.val = super().__new__(cls)
        return cls.val

    def __init__(self):
        """Create a NilType object."""

    def __bool__(self) -> bool:
        return False

    def __hash__(self):
        return 1

    @classmethod
    @annotate
    def eval(cls, namespace: "namespace.Namespace") -> "ENilType":
        """Convert ENil to python ENil(aka return ENil)."""
        return cls()


ENil = ENilType()


class EAllType(EObject):
    """Efus ENil type."""

    val = None

    def __new__(cls):
        """Return or create the singleton ENil."""
        if cls.val is None:
            cls.val = super().__new__(cls)
        return cls.val

    def __init__(self):
        """Create a EAllType object."""

    def __bool__(self) -> bool:
        return False

    def __hash__(self):
        return 1

    @classmethod
    @annotate
    def eval(cls, namespace: "namespace.Namespace") -> "ENilType":
        """Convert EAll to python EAll(aka return EAll)."""
        return cls()

    def __repr__(self):
        return "EAll"


EAll = EAllType()


class ENumber(EObject):
    """Efus Number object."""

    value: int | float

    @annotate
    def eval(self, namespace: "namespace.Namespace") -> int | float:
        """Return the python float or int."""
        return self.value


class EStr(EObject):
    """Efus Integer object."""

    value: str

    @annotate
    def eval(self, namespace: "namespace.Namespace") -> str:
        """Return python string."""
        return self.value % namespace


class EInstr(EObject):
    """Efus instruction base."""

    children: "list[EInstr]"

    @annotate
    def add_child_instruction(self, child: "EInstr") -> None:
        """Add child instruction."""
        self.children.append(child)

    @annotate
    def eval(
        self,
        namespace: "namespace.Namespace",
        parent_component: typing.Optional[component.Component] = None,
    ) -> component.Component:
        """Run the instruction and children in given namespace."""
        self_component = self._eval(namespace, parent_component)
        for child_instruction in self.children:
            child_component = child_instruction.eval(namespace, self_component)
            self_component.add_child_component(child_component)
        return self_component

    @annotate
    def _eval(
        self,
        namespace: "namespace.Namespace",
        parent: typing.Optional[component.Component] = None,
    ) -> component.Component:
        raise NotImplementedError("Override this function please.")


@dataclasses.dataclass
@annotate
class TagDef(EInstr):
    """Tag definition code."""

    name: str
    alias: typing.Optional[str]
    attributes: dict
    children: list[EInstr] = dataclasses.field(default_factory=list)

    @annotate
    def _eval(
        self,
        namespace: "namespace.Namespace",
        parent_component: typing.Optional[component.Component] = None,
    ) -> component.Component:
        try:
            comp_class = namespace.get_name(self.name)
        except NameError as e:
            raise NameError(
                f"Component {self.name!r} could not be"
                + f" found in namespace. (#{e})"
            ) from e
        else:
            comp = comp_class.create(
                namespace, self.attributes, parent_component
            )
            namespace[self.alias] = comp
            return comp


@dataclasses.dataclass
@annotate
class RootDef(EInstr):
    """Tag definition code."""

    children: list[EInstr] = dataclasses.field(default_factory=list)

    @annotate
    def eval(
        self,
        namespace: "namespace.Namespace",
        parent_component: type(None) = None,
    ) -> component.Component:
        ret = None
        for child_instruction in self.children:
            print(child_instruction)
            child_component = child_instruction.eval(namespace, None)
            if child_component is not None:
                ret = child_component
        if "return" in namespace:
            return namespace["return"]
        else:
            return ret


@dataclasses.dataclass
@annotate
class UsingDef(EInstr):
    """Tag definition code."""

    module: str
    names: typing.Optional[tuple[str]]
    is_all: bool
    children: list[EInstr] = dataclasses.field(default_factory=list)

    @annotate
    def eval(
        self,
        namespace: "namespace.Namespace",
        parent_component: typing.Optional[component.Component] = None,
    ) -> type(None):
        namespace.import_module(
            self.module, names="all" if self.is_all else self.names
        )


@annotate
class Efus(EObject):
    """Efus source code base."""

    parent_instruction: EInstr

    @annotate
    def __init__(self, parent_instruction: EInstr):
        """Create efus code object."""
        self.parent_instruction = parent_instruction

    def __repr__(self):
        return str(self.parent_instruction)

    def translate(
        self, namespace: "namespace.Namespace"
    ) -> component.Component:
        """Evaluate the code in the given namespace."""
        return self.parent_instruction.eval(namespace, None)

    eval = translate


@annotate
class EScalar(EObject):
    """Efus variable scalar multiple."""

    coefficient: int | float
    multiple: str

    def __init__(self, coefficient: int | float, multiple: str):
        """Create a scalar multiple of multiple."""
        super().__init__()
        self.coefficient = coefficient
        self.multiple = multiple

    def eval(self, namespace: "namespace.Namespace"):
        """Return the scalar product of multiple and coefficient."""
        return self.coefficient * namespace.get_name(self.multiple)


@annotate
class EPix:
    """
    Efus Pixels class.

    Represents a scalar number of pixels."""

    coeff: int

    @annotate(
        comments=dict(coeff="Pixel coefficient can only be a whole number.")
    )
    def __init__(self, coeff: int = 1):
        """Create a Pixels object."""
        self.coeff = coeff

    def __bool__(self) -> bool:
        return bool(self.coeff)

    def __hash__(self):
        return hash(self.coeff)

    def __mul__(self, other):
        return EPix(self.coeff * int(other))

    __rmul__ = __mul__

    def __imul__(self, other):
        self.coeff *= int(other)

    def __div__(self, other):
        return EPix(self.coeff / int(other))

    __rdiv__ = __div__

    def __idiv__(self, other):
        self.coeff /= int(other)

    def __add__(self, other):
        return EPix(self.coeff + int(other))

    __radd__ = __add__

    def __iadd__(self, other):
        self.coeff += int(other)

    def __sub__(self, other):
        return EPix(self.coeff - int(other))

    __rsub__ = __sub__

    def __isub__(self, other):
        self.coeff -= int(other)

    def __int__(self):
        return self.coeff


px = EPix(1)


@annotate
class ESize(EObject):
    value: tuple[int | float, int | float]

    @annotate
    def __init__(
        self,
        width: int | float | tuple[int | float, int | float] = 0,
        height: int | float = 0,
    ):
        if isinstance(width, tuple):
            self.value = width
        else:
            self.value = (width, height)

    def __iter__(self):
        return iter(self.value)

    def __hash__(self):
        return hash(self.value)

    def __add__(self, other):
        if not isinstance(other, ESize):
            return NotImplemented
        return ESize(tuple(map(sum, zip(self.value, other.value))))

    __radd__ = __add__

    def __iadd__(self, other):
        if not isinstance(other, ESize):
            return NotImplemented
        self.value = (
            self.value[0] + other.value[0],
            self.value[1] + other.value[1],
        )

    def __sub__(self, other):
        if not isinstance(other, ESize):
            return NotImplemented
        return ESize(
            (
                self.value[0] - other.value[0],
                self.value[1] - other.value[1],
            )
        )

    __rsub__ = __sub__

    def __isub__(self, other):
        if not isinstance(other, ESize):
            return NotImplemented
        self.value = (
            self.value[0] - other.value[0],
            self.value[1] - other.value[1],
        )

    def eval(self, namespace: "namespace.Namespace") -> "ESize":
        return self


class EVar(EObject):
    """Efus variable alias."""

    name: str

    def __init__(self, name: str):
        """Create a named variable alias."""
        super().__init__()
        self.name = name

    def eval(self, namespace: "namespace.Namespace") -> typing.Any:
        """Get the given variavle in the namespace."""
        return namespace.get(self.name)
