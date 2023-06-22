import ast
from textwrap import dedent

import hypothesis.strategies as st
from hypothesis import given, settings

from pyodide_pack.ast_rewrite import (
    _strip_module_docstring,
    _StripDocstringsTransformer,
)
from pyodide_pack.testing import _get_stdlib_module_paths


def test_strip_docstrings_function():
    src_code = '''
        def foo():
            """This is a docstring"""
            return 1
        '''
    tree = ast.parse(dedent(src_code))
    tree = _StripDocstringsTransformer().visit(tree)
    assert (
        ast.unparse(tree)
        == dedent(
            """
        def foo():
            return 1"""
        ).strip("\n")
    )


def test_strip_docstrings_nested_functions():
    src_code = '''
        def foo():
            """This is a docstring"""
            def bar():
                """This is a docstring"""
                return 2
            return bar
        '''
    tree = ast.parse(dedent(src_code))
    tree = _StripDocstringsTransformer().visit(tree)
    assert (
        ast.unparse(tree)
        == dedent(
            """
        def foo():

            def bar():
                return 2
            return bar
        """
        ).strip("\n")
    )


def test_strip_docstrings_class():
    src_code = '''
        class A:
            """
            1
            2
            3
            """
            def foo(self):
                """This is a docstring"""
                return 2
            def bar(self):
                """This is a docstring"""
                return 1
        '''
    tree = ast.parse(dedent(src_code))
    tree = _StripDocstringsTransformer().visit(tree)
    assert (
        ast.unparse(tree)
        == dedent(
            """
        class A:

            def foo(self):
                return 2

            def bar(self):
                return 1
        """
        ).strip("\n")
    )


def test_strip_module_docstrings():
    src_code = '''
        """This is a docstring"""
        a = 1
        '''
    tree = ast.parse(dedent(src_code))
    tree = _strip_module_docstring(tree)
    assert (
        ast.unparse(tree)
        == dedent(
            """
        a = 1
        """
        ).strip("\n")
    )


@settings(deadline=300)
@given(st.sampled_from(_get_stdlib_module_paths()))
def test_process_all_stdlib(path):
    """Check that we can process all of the stdlib without crashing."""
    code = path.read_text()

    tree = ast.parse(code)
    tree = _strip_module_docstring(tree)
    tree = _StripDocstringsTransformer().visit(tree)
    ast.unparse(tree)
