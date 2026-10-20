import ast
from pathlib import Path


def extract_function_from_file(filepath: str, function_name: str) -> dict | None:
    """Parses a Python file with AST and extracts the exact source and line bounds of a function."""
    source_text = Path(filepath).read_text(encoding="utf-8")
    source_lines = source_text.splitlines()

    tree = ast.parse(source_text)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            start_line = node.decorator_list[0].lineno if node.decorator_list else node.lineno
            end_line = node.end_lineno
            source = source_lines[start_line - 1 : end_line]
            extracted_source = "\n".join(source)

            return {
                "filepath": filepath,
                "function_name": function_name,
                "start_line": start_line,
                "end_line": end_line,
                "function_source": extracted_source,
            }
    return None


def replace_function_in_file(filepath: str, start_line: int, end_line: int, new_function_code: str) -> None:
    """Replaces lines from start_line to end_line (1-indexed, inclusive) with new_function_code."""
    path = Path(filepath)
    source_lines = path.read_text(encoding="utf-8").splitlines()
    new_lines = new_function_code.strip().splitlines()

    updated_lines = source_lines[:start_line - 1] + new_lines + source_lines[end_line:]
    path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    extracted = extract_function_from_file("target_app/math_ops.py", "calculate_discount")
    if extracted:
        print(f"Extracted {extracted['function_name']} (Lines {extracted['start_line']}–{extracted['end_line']}):\n")
        print(extracted["function_source"])