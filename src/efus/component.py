"""
Base component class and argument manager definitions.

Classes defined here are:
- `CompParams`.
- `CompArgs`
- `Component`
"""

import functools
import inspect
import typing

import efus.parser

from . import namespace
from . import subscribe
from . import types
from pathlib import Path
from pyoload import *
from types import UnionType
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
        computed: dict[str, typing.Any] = {},
    ):
        return CompArgs(self, args, namespace, computed=computed)


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
        values: "dict[str, types.EObject]" = {},
        namespace: "typing.Optional[namespace.Namespace]" = None,
        component: "Component" = None,
        computed: "dict[str, typing.Any]" = {},
    ):
        self.rawvalues = values
        self.namespace = namespace
        dict.__init__(self)
        subscribe.Subscribeable.__init__(self)
        self.subscriber = subscribe.Subscriber()
        self.values = {}
        self.include_values = {}

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
            elif name in computed:
                if types.Binding in _decomposed_union(typespec) and isinstance(
                    val, types.Binding
                ):
                    self.subscriber.subscribe_to(
                        val, lambda s=self, n=name: s.arg_changed(n)
                    )
            else:
                for key, value in dict(values).items():
                    if key.endswith(":") and name.startswith(key):
                        base = value.eval(namespace)

                        for subname in name[len(key) :].split(":"):
                            if subname in base:
                                base = base[subname]
                            else:
                                break
                        self.include_values[name] = base
                        break
                else:
                    self.values[name] = (typespec, default)

        # if len(values) > 0:
        #     raise ValueError(
        #         f"wrong arg {next(iter(values.keys()))}"
        #         + f" for component of type {params.component_name}"
        #     )

    def eval(self):
        self.clear()
        for composite_name, (spec, value) in self.values.items():
            names = composite_name.split(":")
            base = self
            for name in names[:-1]:
                if name not in base:
                    base[name] = dict()
                base = base[name]
            value = self.casts(value, spec)
            base[names[-1]] = value
        for composite_name, value in self.include_values.items():
            names = composite_name.split(":")
            base = self
            for name in names[:-1]:
                if name not in base:
                    base[name] = dict()
                base = base[name]
                base[names[-1]] = value
            else:
                pass
                # print(self.include_values)
        return self

    def __repr__(self):
        return f"CompArgs({dict.__repr__(self)})"

    def casts(
        self, val: typing.Any, spec: typing.Union[typing.Type, typing.Callable]
    ) -> typing.Any:
        if val is types.ENil or spec is types.ENilType:
            return types.ENil
        if typing.get_origin(spec) in (typing.Union, UnionType):
            specs = typing.get_args(spec)

            for spec in specs:
                try:
                    return self.casts(val, spec)
                except NotImplementedError:
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
            elif issubclass(spec, types.EObject) or (
                hasattr(spec, "__has_eobject_casters__")
                and spec.__has_eobject_casters__
            ):
                return spec.cast_from(val)
            elif isinstance(val, types.EObject):
                return val.cast_to(spec, namespace=self.namespace)
            else:
                try:
                    return spec(val)
                except NotImplementedError as e:
                    raise
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
    parent: "typing.Optional[Component]"

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
        assert ret is not None, self.widget
        for child in self.children:
            if child is not None:
                child.render()
        assert ret is not None, self.widget
        return self.postrender() or ret

    def prerender(self):
        pass

    def postrender(self):
        pass


class Comp2nent(Component):
    has_params = True

    def __init_subclass__(cls):
        if hasattr(cls, "ParamsClass"):
            cls.params = efus.component.CompParams.from_class(
                cls.ParamsClass, cls.__name__
            )
        elif cls.has_params:
            raise ValueError(
                "Comp2Nent should have ParamsClass defined, except"
                + " has_params=False"
            )
        cls.get_code()

    @classmethod
    @functools.cache
    def get_code(cls):
        if hasattr(cls, "CODE"):
            return efus.parser.parse_code(cls.CODE)
        else:
            return efus.parser.parse_file(
                str(
                    Path(inspect.getmodule(cls).__file__).parent
                    / (f"{cls.__name__}.efus")
                )
            )

    @annotate
    def __init__(
        self,
        namespace: "typing.Optional[namespace.Namespace]",
        args: CompArgs,
        parent: "typing.Optional[Component]" = None,
    ):
        dict.update(
            namespace,
            {k: getattr(self, k) for k in dir(self) if not k.startswith("_")},
        )
        super().__init__(namespace, args, parent)
        namespace["args"] = self.args
        self.create_composite()  # Something clears self.args here!
        self.init()

    def create_composite(self):
        print(
            "creating_composite start-----------------------",
            id(self.namespace),
        )
        self.component = component = self.get_code().translate(
            self.namespace, self.parent
        )
        print(
            "_________created_composite-----------------------",
            id(self.namespace),
        )
        if "inlet" in self.namespace:
            self.inlet = self.namespace["inlet"]
        else:
            self.inlet = component
        if "outlet" in self.namespace:
            self.outlet = self.namespace["outlet"]
        else:
            self.outlet = None

    def render(self):
        return self.component.render()

    def init(self):
        pass

    def update(self):
        # self.component.update()
        pass

    def __getitem__(self, name: str) -> typing.Any:
        return self.namespace[name]

    def __setitem__(self, name: str, val: typing.Any):
        self.namespace[name] = val

    @classmethod
    @annotate
    def create(
        cls,
        np: namespace.Namespace,
        attrs: dict[str, types.EObject],
        pc: typing.Optional[Component],
    ) -> "Comp2nent":
        from efus.namespace import Namespace

        namespace = Namespace(parents=(np,))
        return cls(np, cls.params.bind(attrs, namespace), pc)

    @classmethod
    @annotate
    def make(cls, attrs: dict[str, typing.Any] = {}) -> "Comp2nent":
        np = namespace.Namespace()
        return cls(
            np,
            cls.params.bind({}, np, computed=attrs),
            None,
        )
