"""
Taktk writeables objects and related stuff.

Composes of:

- `Namespace`
- `Writeable`
- `Expression`
- ...
"""
import builtins
from contextlib import contextmanager
from functools import cached_property
from tkinter import IntVar, StringVar
from typing import Any, Callable, Iterable, Optional

from . import Nil


class Subscribeable:
    """Subscribeable value template."""

    _subscribers: set

    def __init__(self):
        """Create the subscibeable."""
        self._subscribers = set()

    def subscribe(self, subscriber: Callable):
        """Subscribe to the subscibeable."""
        self._subscribers.add(subscriber)

    def unsubscribe(self, subscriber: Callable):
        """Unsunscribe from the namespace."""
        self._subscribers.remove(subscriber)

    def warn_subscribers(self):
        """Call all subscribed handlers."""
        for subscriber in set(self._subscribers):
            subscriber()


class Subscriber:
    """Subscriber object methods."""

    _subscribing: set[tuple[Subscribeable, Callable]]

    def __init__(self):
        """Initialize the subscriber."""
        self._subscribing = set()

    def subscribe_to(self, subscribeable: Subscribeable, callback: Callable):
        """Subscribe to the passed `Subscribeable` with callback."""
        self._subscribing.add((subscribeable, callback))
        subscribeable.subscribe(callback)

    def unsubscribe_from(self, subscribeable: Subscribeable):
        """Unsubscribe all methods from subscribeable."""
        for subscribing in set(self._subscribing):
            subable, call = subscribing
            if subable is subscribeable:
                try:
                    subable.unsubscribe(call)
                except Exception:
                    pass
                finally:
                    self._subscribing.remove(subscribing)

    def unsubscribe_from_all(self):
        """Unsubscribe all methods from all subscribed subscribeable."""
        for subscribing in set(self._subscribing):
            subable, call = subscribing
            try:
                subable.unsubscribe(call)
            except Exception:
                pass
            finally:
                self._subscribing.remove(subscribing)

    def __del__(self):
        """Delete properly the object."""
        self.unsubscribe_from_all()
        super().__del__()


class Namespace(Subscribeable):
    """A parent or child namespace containing variables."""

    parents: "Iterable[Namespace]"
    vars: dict[str]
    _last: dict[str]

    def __init__(self, parents: "Iterable[Namespace]" = []):
        """Create the namespace with the specified parents."""
        self.parents = parents
        self.vars = {}
        self._last = {}
        Subscribeable.__init__(self)

    def __getitem__(self, item: str) -> Any:
        """Get namespace variable from self or parents."""
        self.watch_changes()
        if item in self.vars:
            return self.vars[item]
        else:
            for parent in self.parents:
                try:
                    return parent[item]
                except NameError:
                    continue
            else:
                if item in dir(builtins):
                    return getattr(builtins, item)
                else:
                    raise NameError(item)

    def __setitem__(self, item: str, value: Any):
        """Set namespace variable value."""
        self.vars[item] = value
        self.watch_changes()

    def __repr__(self) -> str:
        """Reproduce the namespace variables."""
        return repr(self.vars)

    def watch_changes(self):
        """Warn subscribers if change noticed."""
        if self.vars != self._last:
            self._last = self.vars.copy()
            self.warn_subscribers()

    @contextmanager
    def save_var(self, varname: str):
        """Context manager to save variable value and restore(only if set!)."""
        try:
            value = self[varname]
        except NameError:
            yield
        else:
            yield
            self[varname] = value

    @contextmanager
    def save(self):
        """Context manager to save variable value and restore(only if set!)."""
        var = self.vars.copy()
        yield
        self.vars.clear()
        self.vars(var)


class Writeable(Subscribeable):
    """Create a Writeable with subscribers and methods."""

    @classmethod
    def from_get_set(
        cls,
        namespace: Namespace,
        getter: str,
        setter: str,
        value: Any = None,
        getter_caller: str = "returns",
        set_name: str = "value",
    ) -> "Writeable":
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
    def from_name(cls, namespace: Namespace, name: str, value: Any = None):
        """Create a writeable object from namespace and name binding."""

        def getter():
            return namespace[name]

        def setter(val):
            namespace[name] = val

        return cls(value, getter, setter)

    def __init__(
        self,
        val: Any = None,
        getter: Optional[Callable] = None,
        setter: Optional[Callable] = None,
    ):
        """Create the object with the specified default value."""
        self._value = val
        self.last = val
        self.subscribers = set()
        self.getter = getter
        self.setter = setter
        Subscribeable.__init__(self)

    def set(self, value: Any):
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
        if self.getter is not None:
            return self.getter()
        else:
            return self._value

    @cached_property
    def intvar(self):
        """Create a `tkinter.IntVar` for Writeable."""
        return WritableIntVar(self)

    @cached_property
    def stringvar(self):
        """Create a `tkinter.StringVar` for Writeable."""
        return WritableStringVar(self)

    @cached_property
    def booleanvar(self):
        """Create a `tkinter.BooleanVar` for Writeable."""
        return WritableBoolVar(self)


class WritableVar(Subscribeable, Subscriber):
    """Writeable tkinter variable binding with automatic updates."""

    _should_update: bool = True
    _should_tk_update: bool = True

    @contextmanager
    def _no_writable_update(self):
        """Prevent updates from writeable."""
        self._should_update = False
        yield
        self._should_update = True

    @contextmanager
    def _no_tk_update(self):
        """Prevent updates from tkinter variable machinery."""
        self._should_tk_update = False
        yield
        self._should_tk_update = True

    def __init__(self, writeable: Writeable):
        """Create a tkinter variable binding to the Writeable."""
        Subscribeable.__init__(self)
        Subscriber.__init__(self)
        self._writable = writeable
        self.subscribe_to(writeable, self._update)
        self.trace_add("write", self._tk_update)

    def _tk_update(self, varname, _, event):
        """Update object from tkinter machinery."""
        if self._should_tk_update:
            with self._no_writable_update():
                self._writable.set(self.get())
                self.set(self._writable.get())


class WritableStringVar(StringVar, WritableVar):
    """A tkinter StringVar binding to a writeable."""

    def __init__(self, writable: Writeable):
        """Create a WritableStringVar binded to `writeable`."""
        super().__init__(value=writable.get())
        WritableVar.__init__(self, writable)

    def _update(self):
        if self._should_update:
            with self._no_tk_update():
                self.set(self._writable.get())


class WritableIntVar(IntVar, WritableVar):
    """A tkinter IntVar binding to a writeable."""

    def __init__(self, writable: Writeable):
        """Create a WritableIntVar binded to `writeable`."""
        super().__init__(value=writable.get())
        WritableVar.__init__(self, writable)

    def _update(self):
        if self._should_update:
            with self._no_tk_update():
                self.set(self._writable.get())


class WritableBoolVar(IntVar, WritableVar):
    """A tkinter BooleanVar binding to a writeable."""

    def __init__(self, writable: Writeable):
        """Create a WritableStringVar binded to `writeable`."""
        super().__init__(value=writable.get())
        WritableVar.__init__(self, writable)

    def _update_(self):
        if self._should_update:
            with self._no_tk_update():
                self.set(bool(self._writable.get()))


# 698663284 rodrige:670932342
