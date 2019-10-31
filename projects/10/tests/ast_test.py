from jack_types import *
from jack_parser import JackParser
from jack_compiler import JackCompiler
import tempfile
from typing import Callable, Any, Tuple
from dataclasses import asdict
import json
import logging
import pytest


def string_to_semantic(s: str,
                       parse_fun: Callable[[JackParser], Semantic]) -> Tuple[Semantic, JackCompiler]:
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                     suffix='.jack') as file:
        file.write(s)
        file.flush()
        engine = JackParser(file.name)
        compiler = JackCompiler(file.name, Class(
            class_name="TEMP",
            class_file_path=file.name,
            variable_declarations=[],
            subroutines=[]
        ))
        return parse_fun(engine), compiler

def print_semantic(obj: Semantic):
    print("\n"+json.dumps(asdict(obj), indent=4))

def test_can_handle_ast():
    print()
    exp, comp = string_to_semantic("1 * 2 + 3 / (4 * 5) + arr[5] + -1 & ~5",
                                   JackParser.parse_expression)

    comp.compile_expression(exp)

