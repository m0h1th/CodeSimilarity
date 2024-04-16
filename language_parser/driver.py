import os
import sys
from typing import List
from datetime import datetime
from tqdm import tqdm
import tree_sitter_python as tspython
import tree_sitter_c as tsc
import ast
from icecream import ic
from pythonast import *
from c_ast import *

from Checker import Checker
from AST import AST, ASTGenerationException, ASTSearchException

def driver(
    AST_class: AST,
    source_filenames: List[str],
    function_name: str,
    function_kind: str,
    threshold: int,
    **kwargs
):

    result = {}

    result["current_datetime"] = str(datetime.now())

    start_time = datetime.now()

    warnings = []
    result["function"] = function_name
    result["warnings"] = warnings

    # Translate all code to ASTs
    print("Parsing files...", file=sys.stderr)
    asts = {}
    for filename in tqdm(source_filenames):
        try:
            ast = AST_class.create(filename, **kwargs)
        except ASTGenerationException:
            warnings.append(f"{filename} cannot be properly parsed")
            continue
        except FileNotFoundError:
            warnings.append(f"{filename} not found")
            continue

        ast.hash_non_recursive()
        asts[os.path.abspath(filename)] = ast

    # Find Sub ASTs based on function name and kind
    function_name = function_name.encode()
    if function_name != b'*':
        print("Filtering partial code...", file=sys.stderr)
        new_asts = {}
        for path in tqdm(asts):
            try:
                sub_ast = asts[path].subtree(function_kind, function_name)
                new_asts[path] = sub_ast
            except ASTSearchException:
                warnings.append(f"{path} doesn't have {function_name}")

        asts = new_asts

    # Run similarity checking algorithm
    checkers = []
    keys = list(asts.keys())

    print("Running plagiarism detection algorithm...", file=sys.stderr)
    with tqdm(total=(1 + len(keys) - 1)*(len(keys)-1)//2) as pbar:
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                path1 = keys[i]
                path2 = keys[j]
                checker = Checker(
                    path1,
                    path2,
                    asts[path1],
                    asts[path2],
                    threshold=threshold,
                )

                checker.check_v2()
                checkers.append(checker)
                pbar.update(1)

    # Collect result
    checker_result = []
    result["result"] = checker_result
    for c in checkers:
        checker_result.append({
            "submission_A": c.path1,
            "submission_B": c.path2,
            "similarity": c.similarity,
            "overlapping_ranges": c.overlapping_ranges,
        })

    # Stop datetime
    end_time = datetime.now()

    # Record total time used
    result["execution_time"] = (end_time - start_time).total_seconds()

    return result


if __name__ == '__main__':
    if sys.argv[1] == "py":
        ast_class = Python_AST
        source_filenames = ["testfiles/file1.py", "testfiles/file2.py"]
        function_name = "fibonacci"
        function_kind = PYTHON_FUNCTION_KIND
        threshold = 5
        result = driver(ast_class, source_filenames, function_name, function_kind, threshold)
        ic(result)
    elif sys.argv[1] == "c":
        ast_class = C_AST
        source_filenames = ["testfiles/file1.c", "testfiles/file2.c"]
        function_name = "fibonacci"
        function_kind = C_FUNCTION_KIND
        threshold = 5
        result = driver(ast_class, source_filenames, function_name, function_kind, threshold)
        ic(result)