import os
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
from typing import List

from language_parser.AST import AST, ASTGenerationException

PYTHON_LANG = Language(tspython.language(), "python")
PYTHON3_FUNCTION_KIND = "FunctionDef"
PYTHON_FUNCTION_KIND = "function_definition"
PYTHON_IDENTIFIER_KIND = "identifier"
PYTHON_COMMENT_KIND = "comment"

PYTHON_IGNORE_KINDS = {
    PYTHON_COMMENT_KIND
}


class Python_AST(AST):
    def __init__(self, parent=None, name=None, text=None, start_pos=None, end_pos=None, kind=None):
        AST.__init__(self, parent, name, text, start_pos, end_pos, kind)

    @classmethod
    def create(cls, path):
        def helper(cursor, parent=None):
            python_ast_node = Python_AST(
                parent=parent,
                name="",
                text=cursor.node.text,
                start_pos=cursor.node.start_point,
                end_pos=cursor.node.end_point,
                kind=cursor.node.type
            )

            if cursor.node.type == PYTHON_FUNCTION_KIND:
                for node in cursor.node.children:
                    if node.type == PYTHON_IDENTIFIER_KIND:
                        python_ast_node.name = node.text
                        break

            python_ast_node.weight = 1

            has_more_children = cursor.goto_first_child()
            if not has_more_children:
                return python_ast_node

            while has_more_children:
                if cursor.node.type in PYTHON_IGNORE_KINDS:
                    has_more_children = cursor.goto_next_sibling()
                    continue

                child_node = helper(cursor, python_ast_node)
                python_ast_node.children.append(child_node)
                python_ast_node.weight += child_node.weight

                has_more_children = cursor.goto_next_sibling()

            cursor.goto_parent()
            return python_ast_node

        with open(path, "rb") as f:
            parser = Parser()
            parser.set_language(PYTHON_LANG)

            tree = parser.parse(f.read())
            cursor = tree.walk()
            return helper(cursor)