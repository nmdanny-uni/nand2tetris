from jack_types import *
from compilation_engine import CompilationEngine
from jack_compiler import JackCompiler
import tempfile
from typing import Callable, Any
from dataclasses import asdict
import json


def string_to_semantic(s: str,
                       parse_fun: Callable[[CompilationEngine], Semantic]) -> Semantic:
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                     suffix='.jack') as file:
        file.write(s)
        file.flush()
        engine = CompilationEngine(file.name)
        return parse_fun(engine)

def test_can_handle_ast():
    print()
    expr = string_to_semantic("1 * 2 + 3 / (4 * 5) + arr[5]",
                              CompilationEngine.parse_expression)
    ast = Expression.from_expression(expr)
    print("\n"+json.dumps(asdict(ast), indent=4))
    for x in ast.iter_postorder_dfs():
        print(x)
