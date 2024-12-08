from pathlib import Path
from abc import ABC
from typing import Tuple, Optional, List, Dict
import re
from enum import Enum, auto
from dataclasses import dataclass

class Instruction:
    pass


class ValType(Enum):
    NUMBER = auto()
    STRING = auto()


@dataclass
class TagDef(Instruction):
    """Tag definition"""
    name: str
    alias: Optional[str]
    attributes: dict

    # def __init__(self, name: str, alias: Optional[str], attributes: dict):
    #     super(TagDef, self).__init__()
    #     self.name = name
    #     self.alias = alias
    #     self.attributes = attributes
        

class Efus:
    instructions: Tuple[Instruction]
    def __init__(self, instrs: Tuple[Instruction]):
        self.instructions = instrs

    def __repr__(self):
        return str(tuple(self.instructions))


class Parser:
    idx: int
    text: str
    instructions: 2
    SPACE = frozenset(" \t")
    tag_def = re.compile(r"(?P<name>[\w]+)(?:\&(?P<alias>[\w]+))?")
    tag_name = re.compile(r"(?P<name>\w[\w\d:]*)\=")
    number = re.compile(r"((?:-|\+)?\d+(?:\.\d+)?)")
    # string = re.compile(r"((\"|')[.+()]\1)")

    class End(Exception):
        pass

    class EOF(End):
        pass

    class EOL(End):
        pass

    class SyntaxError(SyntaxError):
        pass

    def __init__(self):
        self.idx = 0
        self.text = ""
        self.instructions = []
        self.parsed = []

    def feed(self, text: str) -> Tuple[Instruction]:
        """Feed code in parser."""
        self.text += text
        self.go_ahead()
        return self.instructions

    def go_ahead(self):
        while True:  # For each logical line
            print("whyly:", self)
            try:
                indent = self.next_indent()
            except Parser.EOF as e: # Getcha that next line!
                break
            initial = self.idx
            tag = Parser.tag_def.search(self.text, self.idx)
            if tag:
                self.idx += tag.span()[1] - tag.span()[0]
                # print(self.idx, tag.span())
                groups = tag.groupdict()
                attrs = self.parse_attrs()
                self.instructions.append(
                    (indent, TagDef(groups["name"], groups["alias"], attrs))
                )
            else:
                print(self)
                s

    def parse_attrs(self) -> List[Tuple]:
        attrs = []
        try:
            attrs += self.parse_next_attr_value()
        except Parser.End:
            pass
        return attrs

    def parse_next_attr_value(self) -> List[Tuple]:
        self.inline_spaces()
        name = Parser.tag_name.search(self.text, self.idx)
        if name is not None:
            self.idx += name.span()[1] - name.span()[0]
            val = self.parse_next_value()
            return [(name.groupdict()["name"], val)]
        else:
            return []

    def parse_next_value(self):
        if self.text[self.idx].isnumeric() or self.text[self.idx] in "+-":
            if (m := Parser.number.search(self.text, self.idx)):
                self.idx += m.span()[1] - m.span()[0]
                return (ValType.NUMBER, m.groups()[0])
        elif (b := self.text[self.idx]) in "'\"":
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
                raise Parser.SyntaxError("Untermated string at EOF")
            return (ValType.STRING, self.text[begin:self.idx])
        else:
            raise Parser.SyntaxError("Unknown literal")


    def inline_spaces(self):
        while self.idx < len(self.text):
            if self.text[self.idx] in Parser.SPACE:
                self.idx += 1
            elif self.text[self.idx] == "\n":
                raise Parser.EOL()
            else:
                break
        else:
            raise Parser.EOL()

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
            raise Parser.EOF()
        return self.idx - begin

    def __repr__(self):
        begin = (
            self.text.rindex("\n", 0, self.idx) + 1
            if "\n" in self.text[:self.idx]
            else 0
        )
        end   = (
            self.text.index("\n", self.idx)
            if "\n" in self.text[self.idx:]
            else len(self.text)
        )
        pos = self.idx - begin
        return "Parser: %s{\n  | %s\n  | %s^" % (
            self.instructions,
            self.text[begin:end],
            pos*" "
        )


def parse_code(code:str) -> Tuple[Instruction]:
    return Parser().feed(code)


def parse_file(path:str) -> Efus:
    with open(path) as f:
        return Efus(parse_code(f.read()))
