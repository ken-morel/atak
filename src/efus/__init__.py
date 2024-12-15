"""Efus component language parser and utilities."""
from .namespace import Namespace
from .parser import parse_file


def run_file(path: str, namespace: "Namespace"):
    """Run the code in the specified file and return component."""
    code = parse_file(path)
    return code.eval(namespace)
