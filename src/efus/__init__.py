"""Efus component language parser and utilities."""
from .namespace import Namespace
from .parser import parse_file


def run_file(path: str, namespace: "dict | Namespace" = None):
    """Run the code in the specified file and return component."""
    if namespace is None:
        namespace = Namespace()
    elif isinstance(namespace, dict):
        namespace = Namespace(default=namespace)
    code = parse_file(path)
    return code.eval(namespace)
