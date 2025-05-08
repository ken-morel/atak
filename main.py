#!/usr/bin/env python3
"""Main page."""
import pyoload

from typing import Any
from typing import Optional

pyoload.debug()


def main():
    from efus.namespace import Namespace
    from efus.parser import parse_file
    from efus.component import Component, CompArgs, CompParams
    from efus.types import EObject, EScalar, EPix, ESize

    class TkComp(Component):
        namespace: Namespace
        params = CompParams(
            {"title": (str, "no title"), "size": (ESize, ESize(500, 500))}
        )

        def prerender(self):
            from tkinter import Tk

            self.outlet = self.inlet = root = self.widget = Tk()
            root.title(self.args["title"])
            width, height = tuple(self.args["size"])
            root.geometry(f"{width}x{height}")
            return self.widget

        @classmethod
        @pyoload.annotate
        def create(
            cls,
            np: Namespace,
            attrs: dict[str, EObject],
            pc: Optional[Component],
        ) -> Component:
            return cls(np, cls.params.bind(attrs, np), pc)

        def child_geometry(self, child, widget, args):
            widget.pack()

    class TkLabel(Component):
        namespace: Namespace
        params = CompParams(
            {"text": (str, "no text"), "pos": (dict[str, Any], {})}
        )

        def prerender(self):
            from tkinter import Label

            attrs = ("text",)
            self.inlet = self.widget = Label(
                **{x: y for x, y in self.args.items() if x in attrs}
            )
            self.parent.child_geometry(self, self.inlet, self.args["pos"])
            return self.widget

        @classmethod
        @pyoload.annotate
        def create(
            cls,
            np: Namespace,
            attrs: dict[str, EObject],
            pc: Optional[Component],
        ) -> Component:
            return cls(np, cls.params.bind(attrs, np), pc)

    np = Namespace()
    np["tk"] = TkComp
    np["label"] = TkLabel
    code = parse_file("test.efus")
    print(code)

    comp = code.translate(np)

    print(comp)

    widget = comp.render()
    print("renderred", widget)
    widget.mainloop()


try:
    main()
finally:
    print(pyoload.WARN_RET)
