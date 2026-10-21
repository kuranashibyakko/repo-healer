import ast
import difflib
import re
from dotenv import load_dotenv
from groq import Groq
import textwrap

load_dotenv()
groq_client = Groq(timeout=20.0)
MODEL_NAME = "openai/gpt-oss-20b"

def extract_code_block(text: str) -> str:
    """Extracts Python code from markdown fences if present."""
    matches = re.findall(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    return matches[0].strip("\r\n") if matches else text.strip("\r\n")


def generate_unified_diff(old_code: str, new_code: str, filepath: str) -> str:
    """Returns a standard Git-style unified diff string between old_code and new_code."""

    new_lines = new_code.splitlines()
    old_lines = old_code.splitlines()

    unified = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{filepath}",
        tofile=f"b/{filepath}",
        lineterm=""
    )

    return "\n".join(unified)

def generate_function_patch(function_source: str, pytest_output: str) -> str:
    """Prompts the LLM to fix the broken function and validates syntax with ast.parse."""
    system_prompt = (
        "You are an autonomous Python debugging engine.\n"
        "You will be given a broken Python function and the pytest failure traceback.\n"
        "Return ONLY the fixed Python function inside a ```python ... ``` code block.\n"
        "Preserve the exact function name, parameters, and indentation. Do not include test code or explanations."
    )

    user_prompt = (
        f"BROKEN FUNCTION:\n```python\n{function_source}\n```\n\n"
        f"PYTEST FAILURE:\n```\n{pytest_output}\n```\n\n"
        "Provide the corrected function:"
    )

    response = groq_client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
    )

    raw_reply = response.choices[0].message.content or ""
    candidate_code = extract_code_block(raw_reply)
    
    try:
        # Dedent only for syntax validation so indented class methods don't trigger IndentationError
        ast.parse(textwrap.dedent(candidate_code))
        return candidate_code
    except SyntaxError as e:
        raise ValueError(f"Invalid Python syntax generated: {e}") from e

if __name__ == "__main__":
    from ast_surgeon import extract_function_from_file
    from runner import parse_failure_location, run_test_suite

    res = run_test_suite("target_app")
    loc = parse_failure_location(res["output"], "target_app")
    if loc:
        func_info = extract_function_from_file(loc["filepath"], loc["function_name"])
        fixed_code = generate_function_patch(func_info["function_source"], res["output"])
        diff = generate_unified_diff(func_info["function_source"], fixed_code, loc["filepath"])
        print("--- GENERATED GIT DIFF ---")
        print(diff)