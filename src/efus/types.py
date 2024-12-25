"""Efus base and complex types."""
import contextlib
import dataclasses
import functools
import typing

import efus

from . import component

from . import subscribe
from abc import ABC
from pyoload import *


class EObject(ABC, subscribe.Subscribeable):
    """Efus base object value class."""

    def __init__(self, value: typing.Any = None):
        """Initialize default for EObject Subsclasses."""
        if value is not None:
            self.value = value

    @annotate
    def eval(self, namespace: "efus.namespace.Namespace"):
        """Evaluate to a python object."""
        raise NotImplementedError(
            f"Cannot convert object of type {self.__class__.__name__} "
            + "to python ewuivalent."
        )


class ENilType(EObject):
    """Efus ENil type."""

    val = None

    @classmethod
    def cast_from(cls, val: typing.Any):
        return ENil

    def cast_to(self, typ: typing.Any, namespace=None):
        raise NotImplementedError()

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

    def __repr__(self):
        return "ENil"

    @classmethod
    @annotate
    def eval(cls, namespace: "efus.namespace.Namespace") -> "ENilType":
        """Convert ENil to python ENil(aka return ENil)."""
        return cls()


ENil = ENilType()


class EAllType(EObject):
    """Efus ENil type."""

    val = None

    @classmethod
    def cast_from(cls, val: typing.Any):
        raise TypeError("Cannot cast to EAllType")

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
    def eval(cls, namespace: "efus.namespace.Namespace") -> "ENilType":
        """Convert EAll to python EAll(aka return EAll)."""
        return cls()

    def __repr__(self):
        return "EAll"


EAll = EAllType()


@annotate
class ENumber(EObject):
    """Efus Number object."""

    value: int | float

    @classmethod
    def cast_from(cls, val: typing.Any):
        if isinstance(val, float):
            return ENumber(val)
        else:
            return ENumber(int(val))

    def cast_to(self, type: typing.Any, namespace: type(None) = None):
        return type(self.value)

    @annotate
    def eval(self, namespace: "efus.namespace.Namespace") -> int | float:
        """Return the python float or int."""
        return self.value


@annotate
class EStr(EObject):
    """Efus Integer object."""

    value: str

    @classmethod
    def cast_from(cls, val: typing.Any):
        return EStr(str(val))

    def cast_to(self, type: typing.Any, namespace: type(None) = None):
        return type(self.value)

    @annotate
    def eval(self, namespace: "efus.namespace.Namespace") -> str:
        """Return python string."""
        return self.value % namespace


@annotate
class EYamlCode(EObject):
    """Yaml code insertion."""

    code: str

    @annotate
    def __init__(self, code: str):
        """Pass in the yaml code."""
        self.code = code
        lines = code.splitlines()
        ln = lines[0]
        indent = 0
        while ln.startswith(" "):
            indent += 1
        for i in range(len(lines)):
            lines[i] = lines[i][indent:]
        self.code = "\n".join(lines)

    @annotate
    def eval(
        self, namespace: "efus.namespace.Namespace"
    ) -> typing.Union[dict, str, int, list]:
        """Evaluate yaml object or literal."""
        import yaml

        return yaml.safe_load(self.code)


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
        namespace: "efus.namespace.Namespace",
        parent_component: "typing.Optional[component.Component]" = None,
    ) -> "component.Component":
        """Run the instruction and children in given namespace."""
        self_component = self._eval(namespace, parent_component)
        for child_instruction in self.children:
            child_component = child_instruction.eval(namespace, self_component)
            self_component.add_child_component(child_component)
        return self_component

    @annotate
    def _eval(
        self,
        namespace: "efus.namespace.Namespace",
        parent: "typing.Optional[component.Component]" = None,
    ) -> "component.Component":
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
        namespace: "efus.namespace.Namespace",
        parent_component: "typing.Optional[component.Component]" = None,
    ) -> "component.Component":
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
        namespace: "efus.namespace.Namespace",
        parent_component: "typing.Optional[component.Component]" = None,
    ) -> "component.Component":
        ret = None
        with namespace.save():
            namespace["return"] = ENil
            for child_instruction in self.children:
                ret = ret or child_instruction.eval(
                    namespace, parent_component
                )
            if "return" in namespace and namespace["return"] is not ENil:
                return namespace["return"]
            else:
                s
                return ret


@dataclasses.dataclass
@annotate
class UsingDef(EInstr):
    """Tag definition code."""

    module: str
    names: typing.Optional[tuple[str]]
    children: list[EInstr] = dataclasses.field(default_factory=list)

    @annotate
    def eval(
        self,
        namespace: "efus.namespace.Namespace",
        parent_component: "typing.Optional[component.Component]" = None,
    ) -> type(None):
        namespace.import_module(self.module, names=self.names or "all")


@annotate
class Efus(EObject):
    """Efus source code base."""

    parent_instruction: EInstr

    @annotate
    def __init__(self, parent_instruction: EInstr):
        """Create efus code object."""
        self.parent_instruction = parent_instruction

    @annotate
    def __repr__(self):
        return str(self.parent_instruction)

    @annotate
    def translate(
        self,
        namespace: "efus.namespace.Namespace",
        parent: "typing.Optional[component.Component]" = None,
    ) -> "component.Component":
        """Evaluate the code in the given namespace."""
        return self.parent_instruction.eval(namespace, parent)

    eval = translate


@annotate
class EScalar(EObject):
    """Efus variable scalar multiple."""

    coefficient: int | float
    multiple: str

    @classmethod
    def cast_from(cls, val: typing.Any):
        raise NotImplementedError("conversion to EScalar not implemented.")

    def cast_to(
        cls,
        type: typing.Any,
        namespace: "typing.Optional[namespace.Namespace]" = None,
    ):
        return type(self.eval(namespace))

    @annotate
    def __init__(self, coefficient: int | float, multiple: str):
        """Create a scalar multiple of multiple."""
        super().__init__()
        self.coefficient = coefficient
        self.multiple = multiple

    @annotate
    def eval(self, namespace: "efus.namespace.Namespace") -> typing.Any:
        """Return the scalar product of multiple and coefficient."""
        return self.coefficient * namespace.get_name(self.multiple)


@annotate
class EPix:
    """
    Efus Pixels class.

    Represents a scalar number of pixels."""

    coeff: int

    @classmethod
    def cast_from(cls, val: typing.Any):
        return EPix(int(val))

    def cast_to(cls, type: typing.Any, namespace: type(None) = None):
        return type(self.coeff)

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

    @classmethod
    def cast_from(cls, val: typing.Any):
        try:
            return ESize(tuple(val))
        except Exception as e:
            raise TypeError(f"Cannot convert to ESize since {e}") from e

    def cast_to(cls, type: typing.Any, namespace: type(None) = None):
        return type(self.value)

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

    def eval(self, namespace: "efus.namespace.Namespace") -> "ESize":
        return self


@annotate
class EVar(EObject):
    """Efus variable alias."""

    name: str

    @classmethod
    def cast_from(cls, val: typing.Any):
        if isinstance(val, str):
            return EVar(val)
        else:
            raise TypeError("Can only cast str to EVar.")

    def cast_to(
        cls, type: typing.Any, namespace: "efus.namespace.Namespace" = None
    ):
        return type(self.eval(namespace))

    @annotate
    def __init__(self, name: str):
        """Create a named variable alias."""
        super().__init__()
        self.name = name

    @annotate
    def eval(self, namespace: "efus.namespace.Namespace") -> typing.Any:
        """Get the given variavle in the namespace."""
        return namespace.get_name(self.name)

    def __repr__(self):
        return f"EVar({self.name})"


@annotate
class EExpr(EObject):
    """Efus expression."""

    expr: str

    @classmethod
    def cast_from(cls, val: typing.Any):
        if isinstance(val, str):
            return EExpr(val)
        else:
            raise TypeError("Can only cast str to EVar.")

    def cast_to(
        cls, type: typing.Any, namespace: "efus.namespace.Namespace" = None
    ):
        return type(self.eval(namespace))

    @annotate
    def __init__(self, expr: str):
        """Create a named variable alias."""
        super().__init__()
        self.expr = expr

    @annotate
    def eval(self, namespace: "efus.namespace.Namespace") -> typing.Any:
        """Get the given variavle in the namespace."""
        return eval(self.expr, namespace)


@annotate
class Binding(EObject, subscribe.Subscribeable):
    """Create a Writeable with subscribers and methods."""

    @classmethod
    @annotate
    def from_get_set(
        cls,
        namespace: "efus.namespace.Namespace",
        getter: typing.Callable,
        setter: typing.Callable,
        value: typing.Any = None,
        getter_caller: str = "returns",
        set_name: str = "value",
    ) -> "Binding":
        """Create a writeable only using get and set strings."""

        def eval_gets():
            return eval(getter, {}, namespace)

        def call_gets():
            response = None

            def set_response(val):
                nonlocal response
                response = val

            exec(getter, {getter_caller: set_response}, namespace)
            return response

        def call_sets(val):
            with namespace.save_var(set_name):
                namespace[set_name] = val
                exec(setter, {}, namespace)

        return cls(
            value,
            call_gets
            if (len(getter) > 0 and getter[-1] == ";")
            else eval_gets,
            call_sets,
        )

    @classmethod
    def from_name(
        cls,
        namespace: "efus.namespace.Namespace",
        name: str,
        value: typing.Any = None,
    ):
        """Create a writeable object from namespace and name binding."""

        def getter():
            return namespace[name]

        def setter(val):
            namespace[name] = val

        return cls(value, getter, setter)

    def __init__(
        self,
        val: typing.Any = None,
        getter: typing.Optional[typing.Callable] = None,
        setter: typing.Optional[typing.Callable] = None,
    ):
        """Create the object with the specified default value."""
        self._value = val
        self.last = val
        self.subscribers = set()
        self.getter = getter
        self.setter = setter
        subscribe.Subscribeable.__init__(self)

    def set(self, value: typing.Any):
        """Set the value of the Writeable, and watches changes."""
        if self.setter is not None:
            self.setter(value)
        else:
            self._value = value
        self.watch_changes()

    def watch_changes(self) -> bool:
        """
        Check if value changed and notify subscribers.

        Returns if change was noticed
        """
        if self.last != (val := self.get()):
            self.last = val
            self.warn_subscribers()
            return True
        return False

    def get(self):
        """Return the value of the variable."""
        return self.getter()


@annotate
class ENameBinding(Binding):
    name: str

    @classmethod
    def cast_from(cls, val: typing.Any):
        if isinstance(val, str):
            return ENameBinding(val)
        else:
            raise TypeError("Can only cast str to ENameBinding.")

    def cast_to(
        cls, type: typing.Any, namespace: "efus.namespace.Namespace" = None
    ):
        return type(self.eval(namespace))

    @annotate
    def __init__(self, name: str):
        self.name = name

    @annotate
    def eval(
        self, namespace: "efus.namespace.Namespace"
    ) -> "efus.namespace.NameBinding":
        return namespace.create_binding(self.name)
