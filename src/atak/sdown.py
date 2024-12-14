import re
import tkinter as tk
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import pygments
from pyoload import annotate
from ttkbootstrap import Frame, Scrollbar, Text

from . import Nil, NilType, dictionary, resolve
from .component import _Component
from .component.builtin import TkComponent
from .writeable import Expression


class State:
    __slots__ = ("text", "idx")
    text: str
    idx: int

    @annotate
    def __init__(self, text: str, idx: int = 0):
        self.text = text
        self.idx = idx

    def __ior__(self, other: "State"):
        if not isinstance(other, State):
            return NotImplemented
        self.idx = other.idx
        return self

    def copy(self):
        return State(text=self.text, idx=self.idx)

    def __setattr__(self, attr, val):
        if attr == "text" and hasattr(self, "text"):
            raise NotImplementedError()
        else:
            super().__setattr__(attr, val)

    def __int__(self):
        return self.idx

    def __index__(self):
        return self.idx

    def __iadd__(self, val):
        self.idx += val
        return self

    def __add__(self, val):
        return self.idx + val

    def __radd__(self, val):
        return self.idx + val

    def __gt__(self, val):
        return int.__gt__(self.idx, val)

    def __lt__(self, val):
        return int.__lt__(self.idx, val)

    def __hash__(self):
        return self.idx

    def __repr__(self):
        return f"<State:{self.idx}>"

    def __len__(self):
        return len(self.text)

    def __getitem__(self, item):
        if isinstance(item, slice):
            params = tuple(
                self.idx if x is ... else x
                for x in (item.start, item.stop, item.step)
            )
            return self.text.__getitem__(slice(*params))
        elif item is ...:
            return self.text[self]
        else:
            return self.text.__getitem__(item)

    def __bool__(self):
        return self.idx < len(self.text)

    def skip_spaces(self, newline=True):
        while self and self[...].isspace() and (newline or self[...] != "\n"):
            self.idx += 1
        return self

    def next_line(self):
        begin = self.idx
        if "\n" in self[self.idx :]:
            self.idx += self[...:].index("\n")
        else:
            self.idx = len(self.text) - 1
        return self[begin : self.idx]


class Sdown:
    LINK = re.compile(r"^\[([^\]]+)\]\(([^)]+)\)")
    BUTTON = re.compile(r"^\[([^\]]+)\]\(!([^)]+)\)")

    class Tag:
        pass

    @dataclass
    @annotate
    class Text(Tag):
        text: str

        def __hash__(self):
            return hash(self.text)

    @dataclass
    @annotate
    class Italic(Tag):
        text: str

        def __hash__(self):
            return hash(self.text)

    @dataclass
    @annotate
    class Bold(Tag):
        text: str

        def __hash__(self):
            return hash(self.text)

    @dataclass
    @annotate
    class Raw(Tag):
        text: str

        def __hash__(self):
            return hash(self.text)

    @dataclass
    @annotate
    class Emoji(Tag):
        name: str

        def __hash__(self):
            return hash(self.name)

    @dataclass
    @annotate
    class Title(Tag):
        text: str
        level: int

        def __hash__(self):
            return hash(self.text) ** self.level

    @dataclass
    @annotate
    class Link(Tag):
        text: str
        url: str

        def __hash__(self):
            return hash(self.url)

    @dataclass
    @annotate
    class Button(Tag):
        text: str
        command: str

        def __hash__(self):
            return hash(self.text)

    @dataclass
    @annotate
    class Code(Tag):
        text: str
        syntax: str

        def __hash__(self):
            return hash(self.text)

    @dataclass
    class Paragraph(Tag):
        children: "list[Tag]" = field(default_factory=list)

        def __hash__(self):
            return 0

    @dataclass
    class OList(Tag):
        items: "list[list[Tag]]" = field(default_factory=list)

        def __hash__(self):
            return 0

    @dataclass
    class UList(Tag):
        items: "list[list[Tag]]" = field(default_factory=list)

        def __hash__(self):
            return 0

    @classmethod
    def parse_inline_markup(cls, state, tags):
        def add_text(text):
            if len(tags) > 0 and isinstance(tags[-1], cls.Text):
                tags[-1].text += " " + text.strip()
            else:
                tags.append(cls.Text(text))

        while state.skip_spaces(False):
            if state[...] == "_":
                begin = state.copy()
                state += 1
                while state and state[...] != "\n":
                    if state[...] == "_":
                        begin += 1  # skip first quote
                        tags.append(cls.Italic(text=state[begin:...]))
                        state += 1
                        break
                    else:
                        state += 1
                else:
                    add_text(state[begin:...])
                    continue
            elif state[...] == "`":
                begin = state.copy()
                state += 1
                while state and state[...] != "\n":
                    if state[...] == "`":
                        begin += 1  # skip first quote
                        tags.append(cls.Raw(text=state[begin:...]))
                        state += 1
                        break
                    else:
                        state += 1
                else:
                    add_text(state[begin:...])
                    continue
            elif state[...] == ":":
                begin = state.copy()
                state += 1
                while state and state[...] != "\n":
                    if state[...] == ":":
                        begin += 1  # skip first quote
                        tags.append(cls.Emoji(name=state[begin:...]))
                        state += 1
                        break
                    else:
                        state += 1
                else:
                    add_text(state[begin:...])
                    continue
            elif state[...] == "*":
                mode = 1
                begin = state.copy()
                state += 1
                if state and state[...] == "*":
                    mode += 1
                    state += 1
                while state and state[...] != "\n":
                    if state[...:].startswith("*" * mode):
                        begin += mode  # skip first satrisks
                        tags.append(cls.Bold(text=state[begin:...]))
                        state += mode
                        break
                    else:
                        state += 1
                else:
                    add_text(state[begin:...])
                    continue
            elif state[...] == "\n":
                state += 1
                if not state or state[...] != "\n":
                    add_text("\n")
                    continue
                else:
                    break
            elif state[...] == "[":
                if m := cls.BUTTON.search(state[...:]):
                    text, command = m.groups()
                    state += m.span()[1]
                    tags.append(cls.Button(text=text, command=command))
                elif m := cls.LINK.search(state[...:]):
                    text, url = m.groups()
                    state += m.span()[1]
                    tags.append(cls.Link(text=text, url=url))
                else:
                    add_text(state[...])
                    state += 1
            else:
                begin = state.copy()
                while state and state[...] not in "[:*`_\n":
                    state += 1
                add_text(state[begin:...])

    @classmethod
    def parse(cls, text):
        state = State(text)
        tags = []
        while state.skip_spaces():
            if state[...] == "#":  # title
                level = 0
                while state and state[...] == "#":
                    state += 1
                    level += 1
                text = state.skip_spaces().next_line()
                tags.append(cls.Title(text=text, level=level))
            elif state[...] == "-":
                items = []
                state += 1
                while state.skip_spaces(False):
                    line = []
                    cls.parse_inline_markup(State(state.next_line()), line)
                    items.append(line)
                    state += 1
                    if state.skip_spaces(False) and state[...] == "-":
                        state += 1
                    else:
                        break
                tags.append(cls.UList(items=items))
            elif state[...:].startswith("* "):
                items = []
                state += 1
                while state.skip_spaces(False):
                    line = []
                    cls.parse_inline_markup(State(state.next_line()), line)
                    items.append(line)
                    state += 1
                    if state.skip_spaces(False) and state[...] == "*":
                        state += 1
                    else:
                        break
                tags.append(cls.OList(items=items))
            elif state[...:].startswith("```"):
                state += 3
                syntax = state.next_line().strip()
                code = state[...:]
                end = code.find("\n```")
                state += end + 4
                tags.append(cls.Code(text=code, syntax=syntax))
            else:
                paragraph = cls.Paragraph()

                cls.parse_inline_markup(state, paragraph.children)

                tags.append(paragraph)
        return tags


TITLE_FONT = '"Nova Square"'
TEXT_FONT = '"Nova Oval"'
TEXT_SIZE = 10


# @annotate
class SdownViewer(TkComponent):
    _attr_ignore = (
        "text",
        "scrollable",
        "onlink",
        "onbutton",
        "button_class",
    )
    styles = {
        **{
            f"title_{x}": {
                "font": f"{TITLE_FONT} {max(TEXT_SIZE, 35 - (10 * (x - 1)))}",
                "justify": "center" if x < 5 else "left",
                "underline": x > 3,
            }
            for x in range(1, 6)
        },
        "italic": {
            "font": f"{TEXT_FONT} {TEXT_SIZE} italic",
        },
        "raw": {
            "background": "#777",
        },
        "bold": {
            "font": f"{TEXT_FONT} {TEXT_SIZE} bold",
        },
        "plain": {
            "font": f"{TEXT_FONT} {TEXT_SIZE}",
        },
        "link": {
            "font": f"{TEXT_FONT} {TEXT_SIZE} underline",
            "foreground": "#55f",
            "borderwidth": 5,
        },
        "ulist_puce": {
            "font": f"arial 10 bold",
            "foreground": "#ff5",
        },
        "olist_puce": {
            "font": f"arial 10 bold",
            "foreground": "#ff5",
        },
    }

    class Attrs:
        weight: dict = field(default_factory=dict)
        pos: dict = field(default_factory=dict)
        lay: dict = field(default_factory=dict)
        text: str | dictionary.Translation = ""
        width: int | NilType = Nil
        height: int | NilType = Nil
        borderwidth: int | NilType = Nil
        foreground: str | NilType = Nil
        background: str | NilType = Nil
        relief: str | NilType = Nil
        scrollable: bool = True
        onlink: Expression | Callable = lambda link: None
        onbutton: Expression | Callable = lambda link: None
        button_class: Expression | Callable | type(Nil) = Nil

    @contextmanager
    def enabled(self):
        self.widget["state"] = "normal"
        yield
        self.widget["state"] = "disabled"

    def _create(self, parent, params):
        self.container = Frame(parent)
        self.container.columnconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)
        self.container.rowconfigure(0, weight=1)
        params = {
            **{
                self.conf_aliasses[k]: resolve(v)
                for k, v in vars(self.attrs).items()
                if k in self.conf_aliasses and v is not Nil
            }
        }
        self.widget = Text(self.container, **params)
        if self.attrs.scrollable:
            self.scrollbar = Scrollbar(self.container)
            self.scrollbar.grid(column=1, row=0, sticky="nsew")
            self.scrollbar["command"] = self.widget.yview
            self.widget["yscrollcommand"] = self.scrollbar.set
        else:
            self.scrollbar = None
        self.config_styles()
        self.widget["state"] = "disabled"
        self.widget.grid(column=0, row=0, sticky="nsew")
        self.container.columnconfigure(0, weight=1)
        self.marks = {}
        self.links = []
        self.set_text(resolve(self.attrs.text))

    def set_text(self, text):
        self._text = text
        with self.enabled():
            self.clear()
            self.insert_parsed(Sdown.parse(text))

    def add_link(self, url):
        self.links.append(url)
        idx = len(self.links) - 1
        self.widget.tag_bind(f"link_{idx}", "<1>", self.link_opener(url))
        return idx

    def link_opener(self, link):
        def open_link(*_):
            resolve(self.attrs.onlink)(link)

        return open_link

    def commander(self, name):
        def run_command(*_):
            resolve(self.attrs.onbutton)(name)

        return run_command

    def config_styles(self):
        for style, params in self.styles.items():
            self.widget.tag_configure(style, **params)

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self.set_text(text)

    def insert_parsed(self, parsed):
        def insert_inline(tags):
            for tag in tags:
                self.marks[tag] = self.widget.index("end")
                if isinstance(tag, Sdown.Text):
                    self.widget.insert("end", tag.text, ("plain",))
                elif isinstance(tag, Sdown.Italic):
                    self.widget.insert("end", tag.text, ("italic",))
                elif isinstance(tag, Sdown.Bold):
                    self.widget.insert("end", tag.text, ("bold",))
                elif isinstance(tag, Sdown.Raw):
                    self.widget.insert("end", tag.text, ("raw",))
                elif isinstance(tag, Sdown.Emoji):
                    self.widget.insert("end", ":-)", ("emoji",))
                elif isinstance(tag, Sdown.Link):
                    if tag.url not in self.links:
                        self.add_link(tag.url)
                    self.widget.insert(
                        "end",
                        tag.text,
                        (
                            "link",
                            "link_" + str(self.links.index(tag.url)),
                        ),
                    )
                elif isinstance(tag, Sdown.Button):
                    self.widget.window_create(
                        "end",
                        window=self.create_button(
                            text=tag.text, command=self.commander(tag.command)
                        ),
                    )
                else:
                    raise ValueError(f"unknown token {tag!r}")
                self.widget.insert("end", " ")

        def insert_paragraph(paragraph):
            insert_inline(paragraph.children)
            self.widget.insert("end", "\n")

        def insert_ulist(list_):
            for items in list_.items:
                self.widget.insert("end", "\n• ", "ulist_puce")
                insert_inline(items)

        def insert_olist(list_):
            for pos, items in enumerate(list_.items):
                self.widget.insert("end", f"\n{pos + 1} ", "olist_puce")
                insert_inline(items)

        def insert_code(code):
            from pygments import lexers

            component = LexedCode(
                self.namespace,
                self,
                {},
                dict(
                    text=code.text,
                    lexer=lexers.get_lexer_by_name(code.syntax),
                ),
            )
            component.create(self.widget)
            self.widget.window_create("end", window=component.container)

        for tag in parsed:
            if isinstance(tag, Sdown.Title):
                self.widget.insert(
                    "end", tag.text + "\n", (f"title_{tag.level}",)
                )
            elif isinstance(tag, Sdown.Paragraph):
                insert_paragraph(tag)
            elif isinstance(tag, Sdown.UList):
                insert_ulist(tag)
            elif isinstance(tag, Sdown.OList):
                insert_olist(tag)
            elif isinstance(tag, Sdown.Code):
                insert_code(tag)
            else:
                raise ValueError(tag)

    def clear(self):
        self.widget.delete("1.0", "end")
        self.marks.clear()

    def create_button(self, text, command):
        from ttkbootstrap import Button

        return (self.attrs.button_class or Button)(
            master=self.widget, command=command, text=text
        )


class LexedCode(TkComponent):
    _attr_ignore = ("text", "scrollable", "lexer", "style")

    class Attrs:
        pos: dict = field(default_factory=dict)
        lay: dict = field(default_factory=dict)
        text: str | dictionary.Translation = ""
        width: int | NilType = Nil
        height: int | NilType = Nil
        borderwidth: int | NilType = Nil
        foreground: str | NilType = Nil
        background: str | NilType = Nil
        relief: str | NilType = Nil
        scrollable: bool = True
        lexer: Any = Nil
        style: Any = Nil

    @contextmanager
    def enabled(self):
        self.widget["state"] = "normal"
        yield
        self.widget["state"] = "disabled"

    def _create(self, parent, params):
        from pygments import styles

        self.container = Frame(parent)
        self.container.columnconfigure(0, weight=1)
        self.container.rowconfigure(0, weight=1)
        if isinstance(self.attrs.style, dict):
            self._style = self.attrs.style.copy()
            if "name" in self.attrs.style:
                self.style = styles.get_style_by_name(self.attrs.style["name"])
        else:
            self._style = self.attrs.style
            if self.attrs.style is not Nil:
                self.style = self.attrs.style()
            else:
                self.style = next(styles.get_all_styles())
        if isinstance(self.attrs.lexer, dict):
            self._lexer = self.attrs.lexer.copy()
            if "name" in self.attrs.lexer:
                self.lexer = pygments.lexers.get_lexer_by_name(
                    self.attrs.lexer["name"]
                )
            elif "filename" in self.attrs.lexer:
                self.lexer = pygments.lexers.get_for_filename(
                    self.attrs.lexer["filename"]
                )
            elif "mimetype" in self.attrs.lexer:
                self.lexer = pygments.lexers.get_lexer_for_mimetype(
                    self.attrs.lexer["mimetype"]
                )
        else:
            self._lexer = self.attrs.lexer
            if self.attrs.lexer is not Nil:
                self.lexer = self.attrs.lexer()
            else:
                self.lexer = next(pygments.lexers.get_all_lexers())
        self.widget = Text(self.container, **params)
        if self.attrs.scrollable:
            self.scrollbar = Scrollbar(self.container)
            self.scrollbar.grid(column=1, row=0, sticky="nsew")
            self.scrollbar["command"] = self.widget.yview
            self.widget["yscrollcommand"] = self.scrollbar.set
        else:
            self.scrollbar = None
        self.widget["state"] = "disabled"
        self.widget.grid(column=0, row=0, sticky="nsew")
        self.container.rowconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)
        self.set_text(resolve(self.attrs.text))

    def set_text(self, text):
        import pygments

        self._text = text
        with self.enabled():
            self.clear()
            self.insert_tokens(pygments.lex(text, self.attrs.lexer))

    def config_styles(self):
        for style, (fg, bg) in self.attrs.style._styles.items():
            self.widget.tag_configure(style, foreground=fg, background=bg)

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self.set_text(text)

    def insert_tokens(self, tokens):
        for token, text in tokens:
            self.widget.insert("end", text, (str(token),))

    def clear(self):
        self.widget.delete("1.0", "end")
