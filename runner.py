import os
import re
import subprocess
import sys
from pathlib import Path


def run_test_suite(target_dir: str) -> dict:
    """Runs pytest on target_dir and returns a structured result dictionary."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(target_dir).resolve())

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", target_dir, "--tb=short", "-q"],
            capture_output=True,
            text=True,
            timeout=15,
            env=env,
        )
        return {
            "passed": result.returncode == 0,
            "returncode": result.returncode,
            "output": (result.stdout + "\n" + result.stderr).strip(),
        }
    except subprocess.TimeoutExpired as e:
        return {
            "passed": False,
            "returncode": -1,
            "output": f"TimeoutExpired: {e.stdout or ''}",
        }


def parse_failure_location(pytest_output: str, target_dir: str = "target_app") -> dict | None:
    """Extracts the buggy source file, line number, and function name from pytest output."""
    # Case A: Direct stack frame inside a non-test source file (Runtime Exception)
    frame_pattern = r"([^\s:]+\.py):(\d+): in ([a-zA-Z0-9_]+)"
    matches = re.findall(frame_pattern, pytest_output)

    for filepath, line_str, func_name in reversed(matches):
        if not Path(filepath).name.startswith("test_"):
            return {
                "filepath": filepath,
                "line_number": int(line_str),
                "function_name": func_name,
            }

    # Case B: Assertion failure in a test file (Logic bug returning wrong value)
    # Example line: "    assert calculate_discount(100.0, 20.0) == 80.0"
    assert_match = re.search(r"assert\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", pytest_output)
    if assert_match:
        called_func = assert_match.group(1)
        # Search non-test files in target_dir for `def <called_func>(`
        for py_file in Path(target_dir).rglob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            lines = py_file.read_text(encoding="utf-8").splitlines()
            for idx, line in enumerate(lines, start=1):
                if re.match(rf"^\s*def\s+{called_func}\s*\(", line):
                    return {
                        "filepath": py_file.as_posix(),
                        "line_number": idx,
                        "function_name": called_func,
                    }

    return None


if __name__ == "__main__":
    res = run_test_suite("target_app")
    print(f"Tests Passed: {res['passed']}\n")
    print("--- Raw Pytest Output ---")
    print(res["output"])
    print("-------------------------\n")
    if not res["passed"]:
        loc = parse_failure_location(res["output"], "target_app")
        print(f"Detected Bug Location: {loc}")