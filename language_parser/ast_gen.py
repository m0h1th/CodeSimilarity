import tree_sitter_python as tspython
import tree_sitter_c as tsc
from tree_sitter import Language, Parser

PYLANG = Language(tspython.language(), "python")
CLANG = Language(tsc.language(), "c")

filepath = input("Enter file path: ")
if filepath.endswith('.c'):
    LANG = CLANG
else:
    LANG = PYLANG

parser = Parser()
parser.set_language(LANG)

tree = parser.parse(open(filepath, 'rb').read())
print(tree.root_node.sexp())