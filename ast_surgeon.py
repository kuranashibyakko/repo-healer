import ast
from pathlib import Path   

def extract_function_from_file(filepath: str, function_name: str) -> dict | None:
    """Parses a Python file with AST and extracts the exact source and line bounds of a function."""
    source_text = Path(filepath).read_text(encoding="utf-8")
    source_lines = source_text.splitlines()

    tree = ast.parse(source_text)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            start_line = node.lineno
            end_line = node.end_lineno
            source = source_lines[start_line - 1 : end_line]
            extracted_source = "\n".join(source)

            d = {
                "filepath" : filepath,
                "function_name" : function_name,
                "start_line" : start_line,
                "end_line" : end_line,
                "function_source" : extracted_source,
            }
            return d
    return None

if __name__ == "__main__":
    extracted = extract_function_from_file("target_app/math_ops.py", "calculate_discount")
    if extracted:
        print(f"Found {extracted['function_name']} (Lines {extracted['start_line']} to {extracted['end_line']}):\n")
        print(extracted["function_source"])