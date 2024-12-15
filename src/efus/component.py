"""
Base component class and argument manager definitions.

Classes defined here are:
- `CompParams`.
- `CompArgs`
- `Component`
"""

import inspect
import typing

from types import UnionType

from . import namespace
from . import subscribe
from . import types
from pyoload import *
from types import UnionType

ParamDef = dict[
    str,  # name
    tuple[
        typing.Any,  # type
        typing.Any,  # default
    ],
]


@annotate
class CompParams:
    """
    Component parameters holder.

    This class contains the parameters of a component in the form of a
    dictionary mapping of type, default tuples. Like:
    :py:`{"name": (str, "John Doe")}`
    """

    params: dict[str, tuple[typing.Any, typing.Any]]
    component_name: str

    @annotate
    def __init__(self, params: ParamDef, component_name: str):
        """Pass in the parameters to handle."""
        self.params = params
        self.component_name = component_name

    @classmethod
    @annotate
    def from_class(cls, defcls, component_name: str = "<unknown component>"):
        return cls(cls._defs_from_class(defcls), component_name)

    @classmethod
    def _defs_from_class(
        cls, defcls
    ) -> dict[str, tuple[typing.Any, typing.Any]]:
        attrs = {}
        for name, ann in defcls.__annotations__.items():
            attrs[name] = (ann, types.ENil)
        for name, val in vars(defcls).items():
            if not name.startswith("_"):
                if inspect.isclass(val):
                    for subname, spec_and_def in cls._defs_from_class(
                        val
                    ).items():
                        attrs[name + ":" + subname] = spec_and_def
                elif name in attrs:
                    attrs[name] = (attrs[name][0], val)
                else:
                    attrs[name] = (typing.Any, val)
        return attrs

    def bind(
        self,
        args: "dict[str, types.EObject]",
        namespace: "typing.Optional[namespace.Namespace]" = None,
    ):
        return CompArgs(self, args, namespace)


def _decomposed_union(type):
    if typing.get_origin(type) in (typing.Union, UnionType):
        return typing.get_args(type)
    else:
        return (type,)


@annotate
class CompArgs(dict, subscribe.Subscribeable):
    # params: CompParams
    values: "dict[str, types.EObject]"
    namespace: "typing.Optional[namespace.Namespace]"
    subscriber: "subscribe.Subscriber"

    @annotate
    def __init__(
        self,
        params: CompParams,
        values: "dict[str, types.EObject]",
        namespace: "typing.Optional[namespace.Namespace]" = None,
        component: "Component" = None,
    ):
        self.rawvalues = values
        self.namespace = namespace
        dict.__init__(self)
        subscribe.Subscribeable.__init__(self)
        self.subscriber = subscribe.Subscriber()
        self.values = {}
        for name, (typespec, default) in params.params.items():
            if name in values:
                val = self.values[name] = (
                    typespec,
                    values[name].eval(namespace),
                )
                if types.Binding in _decomposed_union(typespec) and isinstance(
                    val, types.Binding
                ):
                    self.subscriber.subscribe_to(
                        val, lambda s=self, n=name: s.arg_changed(n)
                    )
                values.pop(name)
            else:
                self.values[name] = (typespec, default)
        if len(values) > 0:
            raise ValueError(
                f"wrong arg {next(iter(values.keys()))} for component of type {params.component_name}"
            )

    def eval(self):
        self.clear()
        print("VALUES" * 10, self.values)
        for composite_name, (spec, value) in self.values.items():
            names = composite_name.split(":")
            base = self
            for name in names[:-1]:
                if name not in base:
                    base[name] = dict()
                base = base[name]
            value = self.casts(value, spec)
            base[names[-1]] = value
        return self

    def __repr__(self):
        return f"CompArgs({dict.__repr__(self)})"

    def casts(
        self, val: typing.Any, spec: typing.Union[typing.Type, typing.Callable]
    ) -> typing.Any:
        if typing.get_origin(spec) in (typing.Union, UnionType):
            specs = typing.get_args(spec)

            for spec in specs:
                try:
                    return self.casts(val, spec)
                except Exception:
                    pass
        elif typing.get_origin(spec) in (dict, typing.Dict):
            keyt, valt = typing.get_args(spec)
            return {
                self.casts(k, keyt): self.casts(v, valt)
                for k, v in val.items()
            }
        else:
            if type_match(val, spec)[0]:
                return val
            elif issubclass(spec, types.EObject):
                return spec.cast_from(val)
            elif isinstance(val, types.EObject):
                return val.cast_to(spec, namespace=self.namespace)
            else:
                try:
                    return spec(val)
                except Exception:
                    pass
                raise NotImplementedError(val, spec)

    @annotate
    def arg_changed(self, name: str):
        self.eval(only_name=name)
        self.warn_subscribers()
        return self


@annotate
class Component(subscribe.Subscriber):
    namespace: "namespace.Namespace"
    subscriber: "subscribe.Subscriber"
    args: CompArgs
    children: "list[Component]"
    parent: "Component"

    def add_child_component(self, component: "Component"):
        """Add `component` to self children."""
        self.children.append(component)

    @annotate
    def __init__(
        self,
        namespace: "namespace.Namespace",
        args: CompArgs | typing.Callable,
        parent: "typing.Optional[Component]" = None,
    ):
        if callable(args):
            args = args(self)
        self.args = args
        args.eval()
        self.subscriber = subscribe.Subscriber()
        self.namespace = namespace
        self.subscriber.subscribe_to(args, self.update)
        self.parent = parent
        self.children = []
        self.init()

    @annotate
    def _namespace_change(self):
        self.args.eval()
        self.update()

    def init(self):
        pass

    def render(self):
        ret = self.prerender()
        for child in self.children:
            if child is not None:
                child.render()
        return self.postrender() or ret

    def prerender(self):
        return True

    def postrender(self):
        pass
