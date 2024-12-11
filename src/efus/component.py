"""Base component class."""

from . import types, namespace, subscribe
import typing

ParamDef = dict[
    str,  # name
    tuple[
        typing.Type,  # type
        typing.Any,  # default
    ],
]


class CompParams:
    params: list[ParamDef]

    def __init__(self, params: ParamDef):
        self.params = params

    def bind(self, args: tuple, kw: dict[str, types.EObject]):
        return CompArgs(self, args, kw)


class CompArgs(dict):
    params: ParamDef

    def __init__(
        self, params: CompParams, values: list[tuple[str, types.EObject]]
    ):
        self.params = params
        self.values = values
        super().__init__()

    def eval(self, namespace: namespace.Namespace) -> typing.Self:
        self.clear()
        vals = {}
        for name, val in self.values:
            names = name.split(":")
            base = vals
            for sub_name in names[:-1]:
                if sub_name not in base:
                    base[sub_name] = dict()
                elif not isinstance(base[sub_name], dict):
                    base[sub_name] = dict(_val=base[sub_name])
            base[names[-1]] = val.eval(namespace)
        return self


class EComponent(subscribe.Subscriber):
    namespace: namespace.Namespace
    subscriber: namespace.Subscriber

    def __init__(self):
        self.subscriber = subscribe.Subscriber()
        self.namespace = namespace.Namespace()
        self.subscriber.subscribe_to(namespace, self._namespace_change)

    def _namespace_change(self):
        self.update()
