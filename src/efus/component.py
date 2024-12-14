"""
Base component class and argument manager definitions.

Classes defined here are:
- `CompParams`.
- `CompArgs`
- `Component`
"""

import typing

from . import namespace
from . import subscribe
from . import types
from pyoload import *

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

    params: ParamDef

    @annotate
    def __init__(self, params: ParamDef):
        """Pass in the parameters to handle."""
        self.params = params

    @classmethod
    def from_class(cls, defcls):
        attrs = {}
        for name, ann in defcls.__annotations__.items():
            attrs[name] = (ann, types.ENil)
        for name, val in vars(defcls).items():
            if name[0] != "_":
                if name in attrs:
                    attrs[name] = (attrs[name][0], val)
                else:
                    attrs[name] = (typing.Any, val)
        return cls(attrs)

    def bind(
        self,
        args: "dict[str, types.EObject]",
        namespace: "typing.Optional[namespace.Namespace]" = None,
    ):
        return CompArgs(self, args, namespace)


@annotate
class CompArgs(dict, subscribe.Subscribeable):
    params: CompParams
    values: "dict[str, types.EObject]"
    namespace: "typing.Optional[namespace.Namespace]"

    @annotate
    def __init__(
        self,
        params: CompParams,
        values: "dict[str, types.EObject]",
        namespace: "typing.Optional[namespace.Namespace]" = None,
    ):
        self.params = params
        self.values = values
        self.namespace = namespace
        dict.__init__(self)
        subscribe.Subscribeable.__init__(self)

    @annotate
    def eval(
        self, namespace: "typing.Optional[namespace.Namespace]" = None
    ) -> "CompArgs":
        namespace = namespace or self.namespace
        if namespace is None:
            raise TypeError("No namespace specified to evaluate arguments.")
        self.clear()
        vals = {}
        for name, val in self.values.items():
            names = name.split(":")
            if names[0] not in self.params.params:
                raise ValueError(f"Wrong attr {name}.")
            base = vals
            for sub_name in names[:-1]:
                if sub_name not in base:
                    base[sub_name] = dict()
                elif not isinstance(base[sub_name], dict):
                    base[sub_name] = dict(_val=base[sub_name])
                base = base[sub_name]
            base[names[-1]] = val
        final = {}
        for name, (spec, default) in self.params.params.items():
            if name in vals:
                value = vals[name]
                final[name] = self.casts(
                    spec,
                    value.eval(self.namespace)
                    if isinstance(value, types.EObject)
                    else value,
                )
            else:
                final[name] = default
        m, msg = type_match(final[name], spec)
        if not m:
            raise TypeError(
                f"Value does not conform to parameter {name!r}:{spec}"
                + f". Pyoload says: {msg or 'Nothing else.'}",
            )
        self.update(final)
        return self

    def __repr__(self):
        return f"CompArgs({dict.__repr__(self)})"

    def casts(
        self, spec: typing.Union[typing.Type, typing.Callable], val: typing.Any
    ) -> typing.Any:
        if type_match(val, spec):
            return val
        else:
            raise NotImplementedError()


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
        args: CompArgs,
        parent: "typing.Optional[Component]" = None,
    ):
        self.args = args
        self.subscriber = subscribe.Subscriber()
        self.namespace = namespace
        self.subscriber.subscribe_to(namespace, self._namespace_change)
        self.parent = parent
        self.children = []
        args.eval()
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
