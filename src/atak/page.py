import json
import re
import string
from decimal import Decimal
from importlib import import_module
from logging import getLogger
from tkinter import Tk, Widget
from types import ModuleType
from typing import Any, Optional
from urllib.parse import parse_qsl, urlparse
from uuid import UUID

from pyoload import annotate

from . import application, component
from . import store as store_

log = getLogger(__name__)


HANDLER_NAME = set(string.ascii_letters + "_")
DEFAULT_HANDLER = "default"


@annotate
class PageView:
    """
    Applictaions page view, performs page routing, caching and history for a
    taktk application.
    """

    history: list
    current_page: Any
    app: "application.Application"
    store: store_.Store
    destroy_cache: int
    package: ModuleType
    current_url: Optional[str]

    def __init__(
        self,
        parent: Tk | Widget,
        page: ModuleType,
        app: "application.Application",
        destroy_cache: int = 5,
    ):
        """\
        :param parent: the parent widget to view the pages in, usually the
        outlet of an apps layout.

        :param page: The module the app will fetch pages from.

        :param destroy_cache: Experimental destroy cache
        """
        self.history = []
        self.current_page = None
        self.parent = parent
        self.current_widget = None
        self.app = app
        self.store = app.store
        self.destroy_cache = destroy_cache
        self.package = page
        self.current_url = None

    def geometry(self):
        """\
        Prepares the parent's geometry.
        """
        self.parent.columnconfigure(0, weight=1)
        self.parent.rowconfigure(0, weight=1)

    def url(self, url: str, redirect: bool = True):
        """
        Targets the app to the url following redirects except
        redirect parameter set to false.

        :raises taktk.pages.Redirect: In case redrect set to false and a
        redirect occured
        """
        target = url
        while True:
            try:
                result = self.exec_url(target)
            except Redirect as r:
                target = r.url
                if not redirect:
                    raise
            else:
                return result

    def view_component(self, components: "tuple", *, _cache={}):
        if self.current_page is None:
            self.current_page = 0
        else:
            self.current_page += 1
        current = self.current_widget
        self.history.insert(self.current_page, components)
        parent = self.parent
        master = None
        for component in components:
            if isinstance(component, type):
                if component not in _cache:
                    _cache[component] = component()
                component = _cache[component]

            component = component
            parent.columnconfigure(0, weight=1)
            parent.rowconfigure(0, weight=1)
            component.render(parent)
            container = component.container
            container.grid(column=0, row=0, sticky="nsew")
            master = master or container
            parent = component.outlet
        self.current_widget = master
        if current is not None:
            self.destroy_later(master)

    def destroy_later(self, widget, cache=[]):
        cache.append(widget)
        if len(cache) > self.destroy_cache:
            cache.pop(0).destroy()

    def back(self):
        if self.current_page > 0:
            self.focus_page(self.current_page - 1)
            return True
        else:
            return False

    def forward(self):
        if self.current_page < len(self.history) - 1:
            self.focus_page(self.current_page + 1)
            return True
        else:
            return False

    def focus_page(self, idx):
        page = self.history[idx]
        if self.current_widget is not None:
            self.current_widget.destroy()
        self.history[idx].render(self.parent)
        self.current_widget = self.history[idx].container
        self.current_widget.grid(column=0, row=0, sticky="nsew")
        self.current_page = idx

    def exec_url(self, cmd):
        if cmd.strip("/") == "!current":
            return (
                None,
                {
                    "ok": True,
                    "url": self.current_url,
                },
            )
        elif cmd.strip("/") == "!back":
            return (
                None,
                {
                    "ok": True,
                    "changed": self.back(),
                    "url": self.current_url,
                },
            )
        elif cmd.strip("/") == "!forward":
            return (
                None,
                {
                    "ok": True,
                    "changed": self.forward(),
                    "url": self.current_url,
                },
            )
        else:
            parsed = urlparse(cmd)
            args = {k: json.loads(v) for k, v in parse_qsl(parsed.query)}
            handler = parsed.fragment
            path = parsed.path
            if (
                "@" in path
                and len(set(path[path.index("@") + 1 :]) - HANDLER_NAME) == 0
            ):
                path, handler = path.rsplit("@", 1)
            self.current_url = parsed.path
            return self(path, handler, args)

    def __call__(self, module, handler, params={}, /, **kwparams):
        from .component import Component

        if isinstance(module, str):
            module, urlparams, layouts = self.import_module(module)
        try:
            function = getattr(module, handler or DEFAULT_HANDLER)
        except AttributeError as e:
            raise Error404(e)
        http = comp = None
        page = function(
            self.store,
            *urlparams,
            **kwparams,
        )
        if page is None:
            return (None, None)
        elif isinstance(page, tuple):
            comp, http = page
        elif isinstance(page, Component):
            comp = page
        else:
            http = page
        if comp is not None:
            layouts.append(comp)
            self.view_component(tuple(layouts))
        return (tuple(layouts), http)

    def import_module(self, path):
        module = self.package
        params = []
        layouts = []
        if hasattr(module, "layout"):
            layouts.append(module.layout)
        for package in path.strip("/").split("/"):
            if not package.strip():
                continue
            try:
                module = import_module(module.__package__ + "." + package)
            except ImportError:
                for regex, name, converter in URLPATTERNS:
                    if match := regex.fullmatch(package):
                        try:
                            module = import_module(
                                module.__package__ + "." + name
                            )
                        except ImportError:
                            continue
                        else:
                            try:
                                param = converter(package)
                            except:
                                raise Error404()
                            else:
                                params.append(param)
                            break
                else:
                    raise Error404(path)
            if hasattr(module, "layout"):
                layouts.append(module.layout)

        return module, params, layouts


class Error404(ValueError):
    pass


class Redirect(Exception):
    def __init__(self, url: str):
        self.url = url
        super().__init__()


SHORTCUTS = {
    "int": re.compile(r"^\d+$"),
    "decimal": re.compile(r"^\d+\.\d+$"),
    "str": re.compile(r".+"),
    "uuid": re.compile(
        r"[\da-f]{8}\-[\da-f]{4}\-[\da-f]{4}\-[\da-f]{4}\-[\da-f]{12}",
    ),
}
URLPATTERNS = [
    ("int", int),
    ("decimal", Decimal),
    ("str", str),
    ("uuid", UUID),
]
URLPATTERNS = [(SHORTCUTS[n], n, c) for n, c in URLPATTERNS]


def register_urlpattern(regex, converter=None, name=None, position=-2):
    def registerrer(func):
        nonlocal name, regex
        if name is None:
            name = func.__name__.lower()
        if len(regex) > 2 and regex[0] == "<" and regex[-1] == ">":
            try:
                regex = SHORTCUTS[regex[1:-1]]
            except IndexError:
                raise ValueError(f"Unknown url shortcut: {regex!r}")
        elif not isinstance(regex, re.Pattern):
            regex = re.compile(regex)
        URLPATTERNS.insert(position, (regex, "_" + name, func))

    if converter is not None:
        return registerrer(converter)
    else:
        return registerrer
