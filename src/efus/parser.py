"""Efus parser class and functions."""
import re

from . import types
from pyoload import *
from typing import Optional


@annotate
class Parser:
    """Efus code parser class."""

    idx: int
    text: str
    tree: "list[tuple[int, types.EInstr]]"
    file: Optional[str]
    SPACE = frozenset(" \t")
    STRING_QUOTE = format("\"'")
    TAML_TOKEN = ("---\n", "\n...")
    tag_def = re.compile(r"(?P<name>[\w]+)(?:\&(?P<alias>[\w]+))?(?=$|\s|\n)")
    tag_name = re.compile(r"(?P<name>\w[\w\d\:]*)\=")
    decimal = re.compile(r"([+\-]?\d+(?:\.\d+)?)(?=$|\s|\n)")
    integer = re.compile(r"([+\-]?\d+)(?=$|\s|\n)")
    size = re.compile(r"(\d+)x(\d+)(?=$|\s|\n)")
    scalar = re.compile(r"([+\-]?\d+)(\.\d+)?(\w[\w\d]*)(?=$|\s|\n)")
    const_var = re.compile(r"([a-zA-Z][a-zA-Z1-9]*)(?=$|\s|\n)")
    using = re.compile(
        r"using\s+([\w\d\.]+)(?:(?:\:\s*(\*))|(?:\:\s*([\w\d ]+)))?"
        + r"(?=\s*$|\s*\n)"
    )
    # string = re.compile(r"((\p"|')[.+()]\1)")

    class _End(Exception):
        pass

    class _EOF(_End):
        pass

    class _EOL(_End):
        pass

    class SyntaxError(SyntaxError):
        """Efus code syntax error."""

    @annotate
    def __init__(self, file: str = None):
        """Create an efus code parser with optional given file."""
        self.idx = 0
        self.text = ""
        self.tree = [(-1, types.RootDef())]
        self.parsed = []
        self.file = file

    @annotate
    def feed(self, text: str) -> "types.RootDef":
        """Feed code in parser."""
        self.text += text
        self.go_ahead()
        return self.tree[0][1]

    @annotate
    def go_ahead(self):
        """Read and interpret the next instructions."""
        while True:  # For each logical line
            try:
                indent = self.next_indent()
            except Parser._EOF:  # Getcha that next line!
                break
            if (
                using := Parser.using.search(self.text, self.idx)
            ) is not None and using.span()[0] == self.idx:
                self.idx += using.span()[1] - using.span()[0]
                module = using.groups()[0]
                names = using.groups()[2]
                if names is not None:
                    names = tuple(map(str.strip, names.split(",")))
                self._queue_instr(indent, types.UsingDef(module, names))
            elif (
                tag := Parser.tag_def.search(self.text, self.idx)
            ) is not None and tag.span()[0] == self.idx:
                self.idx += tag.span()[1] - tag.span()[0]
                groups = tag.groupdict()
                attrs = dict(self.parse_attrs())
                tag = types.TagDef(groups["name"], groups["alias"], attrs)
                self._queue_instr(indent, tag)
            else:
                raise Exception()

    @annotate
    def _queue_instr(self, indent: int, instr: "types.EInstr"):
        if len(self.tree) == 0:
            self.tree = [(indent, instr)]
        else:
            if indent > self.tree[-1][0]:  # it is a child of -1
                self.tree[-1][1].add_child_instruction(instr)
                self.tree.append((indent, instr))
            elif indent == self.tree[-1][0]:  # -1 and instr are both
                if len(self.tree) >= 2:
                    self.tree[-2][1].add_child_instruction(instr)
                self.tree[-1] = (indent, instr)
            else:  # instr is higher in hieharchy but after -1
                while indent <= self.tree[-1][0]:
                    self.tree.pop()  # remove all to parent
                    if len(self.tree) == 0:
                        raise Parser.SyntaxError(
                            f"Fatal: Code has two heads\n{self}"
                        )
                self.tree[-1][1].add_child_instruction(instr)
                self.tree.append((indent, instr))

    @annotate
    def parse_attrs(self) -> "list[tuple[str, types.EObject]]":
        """Parse next following attrs.."""
        attrs = []
        try:
            while True:
                attrs += self.parse_next_attr_value()
        except Parser._EOL:
            pass
        return attrs

    @annotate
    def parse_next_attr_value(self) -> list[tuple]:
        self.inline_spaces()
        name = Parser.tag_name.search(self.text, self.idx)
        if name is not None:
            self.idx += name.span()[1] - name.span()[0]
            val = self.parse_next_value()
            return [(name.groupdict()["name"], val)]
        else:
            return []

    def parse_next_value(self):
        if self.text[self.idx :].startswith(Parser.YAML_TOKEN[0]):
            self.idx += 4
            begin = self.idx
            end = self.text.find(Parser.YAML_TOKEN[1], self.idx)
            if end == -1:
                raise Parser.SyntaxError(
                    "Untermated yaml markup", self.py_stack()
                )
            else:
                self.idx = end + len(Parser.YAML_TOKEN[1])
                return types.EYamlCode(self.text[begin:end])
        elif (m := Parser.const_var.search(self.text, self.idx)) and m.span()[
            0
        ] == self.idx:
            self.idx += m.span()[1] - m.span()[0]
            return types.EVar(m.groups()[0])
        elif (m := Parser.size.search(self.text, self.idx)) and m.span()[
            0
        ] == self.idx:
            self.idx += m.span()[1] - m.span()[0]
            return types.ESize(int(m.groups()[0]), int(m.groups()[1]))
        elif (m := Parser.decimal.search(self.text, self.idx)) and m.span()[
            0
        ] == self.idx:
            self.idx += m.span()[1] - m.span()[0]
            return types.ENumber(float(m.groups()[0]))
        elif (m := Parser.integer.search(self.text, self.idx)) and m.span()[
            0
        ] == self.idx:
            self.idx += m.span()[1] - m.span()[0]
            return types.ENumber(int(m.groups()[0]))
        elif (m := Parser.scalar.search(self.text, self.idx)) and m.span()[
            0
        ] == self.idx:
            self.idx += m.span()[1] - m.span()[0]
            whole, decimal, multiple = m.groups()
            if decimal is not None:
                return types.EScalar(float(whole + decimal), multiple)
            else:
                return types.EScalar(int(whole), multiple)
        elif (b := self.text[self.idx]) in Parser.STRING_QUOTE:
            begin = self.idx
            self.idx += 1
            while self.idx < len(self.text):
                if self.text[self.idx] == b:
                    self.idx += 1
                    break
                elif self.text[self.idx] == "\\":
                    self.idx += 2
                elif self.text[self.idx] == "\n":
                    raise Parser.SyntaxError("Untermated string before EOL")
                else:
                    self.idx += 1
            else:
                raise Parser.SyntaxError("Untermated string at _EOF")
            return types.EStr(eval(self.text[begin : self.idx]))
        elif self.text[self.idx] == "(":
            begin = self.idx + 1
            quotes = []
            while self.idx < len(self.text):
                if (
                    len(quotes) > 0
                    and quotes[-1] in Parser.STRING_QUOTE
                    and self.text[self.idx] == "\\"
                ):
                    self.idx += 1
                elif self.text[self.idx] in Parser.STRING_QUOTE:
                    if len(quotes) > 0 and quotes[-1] == self.text[self.idx]:
                        quotes.pop()
                    else:
                        quotes.append(self.text[self.idx])
                elif self.text[self.idx] == "(":
                    quotes.append("(")
                elif self.text[self.idx] == ")":
                    quotes.pop()
                    if len(quotes) == 0:
                        self.idx += 1
                        break
                self.idx += 1
            else:
                raise Parser.SyntaxError("Untermated expr at EOF")
            return types.EExpr(self.text[begin : self.idx - 1])
        elif self.text[self.idx] == "&":
            self.idx += 1
            begin = self.idx
            if self.text[self.idx] == "(":
                raise NotImplementedError
            else:
                while (
                    self.idx < len(self.text)
                    and not self.text[self.idx].isspace()
                ):
                    self.idx += 1
                return types.ENameBinding(self.text[begin : self.idx])

        else:
            raise Parser.SyntaxError("Unknown literal\n" + self.py_stack())

    def inline_spaces(self):
        while self.idx < len(self.text):
            if self.text[self.idx] in Parser.SPACE:
                self.idx += 1
            elif self.text[self.idx] == "\n":
                raise Parser._EOL()
            else:
                break
        else:
            raise Parser._EOL()

    def next_indent(self) -> int:
        begin = self.idx
        while self.idx < len(self.text):
            if self.text[self.idx] in Parser.SPACE:
                self.idx += 1
            elif self.text[self.idx] == "\n":
                self.idx += 1
                begin = self.idx
            else:
                break
        else:
            self.idx = begin
            raise Parser._EOF()
        return self.idx - begin

    def __repr__(self):
        begin = (
            self.text.rindex("\n", 0, self.idx) + 1
            if "\n" in self.text[: self.idx]
            else 0
        )
        end = (
            self.text.index("\n", self.idx)
            if "\n" in self.text[self.idx :]
            else len(self.text)
        )
        pos = self.idx - begin
        return "Parser: %s{\n  | %s\n  | %s^" % (
            self.instructions,
            self.text[begin:end],
            pos * " ",
        )

    def py_stack(self) -> str:
        """Create a python-like stack."""
        begin = (
            self.text.rindex("\n", 0, self.idx) + 1
            if "\n" in self.text[: self.idx]
            else 0
        )
        end = (
            self.text.index("\n", self.idx)
            if "\n" in self.text[self.idx :]
            else len(self.text)
        )
        pos = self.idx - begin
        ln = self.text[: self.idx].count("\n") + 1
        return '  File "%s", line %d, column %d\n  %s\n  %s^' % (
            self.file or "<string>",
            ln,
            pos,
            self.text[begin:end],
            pos * " ",
        )


@annotate
def parse_file(path: str) -> "types.Efus":
    with open(path) as f:
        return parse_code(f.read(), path)


@annotate
def parse_code(code: str, file: str = "<string>") -> "types.Efus":
    return types.Efus(Parser(file).feed(code))
