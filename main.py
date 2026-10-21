import sys
from pathlib import Path

from ast_surgeon import extract_function_from_file, replace_function_in_file
from healer import generate_function_patch, generate_unified_diff
from runner import parse_failure_location, run_test_suite


def heal_repository(target_dir: str, max_attempts: int = 3) -> bool:
    """Autonomously diagnoses, patches, and verifies a buggy Python directory."""
    print(f"🔍 [Repo-Healer] Scanning '{target_dir}'...")

    for attempt in range(1, max_attempts + 1):
        print(f"\n--- [Healing Cycle {attempt}/{max_attempts}] ---")

        # 1. Run the test suite
        test_res = run_test_suite(target_dir)
        if test_res["passed"]:
            print("✅ All tests passing! Repository is healthy.")
            return True

        # 2. Locate the bug
        loc = parse_failure_location(test_res["output"], target_dir)
        if not loc:
            print("❌ Could not pinpoint a specific source function from pytest output.")
            print(test_res["output"])
            return False

        filepath = loc["filepath"]
        func_name = loc["function_name"]
        print(f"🎯 Pinpointed failure in `{filepath}` -> `{func_name}()` (Line {loc['line_number']})")

        # 3. Extract the broken function via AST
        func_info = extract_function_from_file(filepath, func_name)
        if not func_info:
            print(f"❌ AST Surgeon could not locate `{func_name}` in `{filepath}`.")
            return False

        # Snapshot the original file in memory for rollback safety
        file_path_obj = Path(filepath)
        original_file_backup = file_path_obj.read_text(encoding="utf-8")

        # 4. Generate the patch
        try:
            fixed_code = generate_function_patch(func_info["function_source"], test_res["output"])
        except ValueError as e:
            print(f"⚠️ Patch generation failed: {e}")
            continue

        # Display the unified Git diff
        diff = generate_unified_diff(func_info["function_source"], fixed_code, filepath)
        print("\n--- [PROPOSED PATCH DIFF] ---")
        print(diff)
        print("-----------------------------\n")

        # 5. Surgically splice the patch into the source file
        replace_function_in_file(filepath, func_info["start_line"], func_info["end_line"], fixed_code)
        print(f"💉 Spliced patch into `{filepath}`. Verifying with test suite...")

        # 6. Re-run tests to verify the fix
        verify_res = run_test_suite(target_dir)
        if verify_res["passed"]:
            print(f"🎉 Verification successful! `{func_name}()` healed and all tests passed.")
            return True
        else:
            print("⚠️ Verification failed. Rolling back changes to preserve codebase state...")
            file_path_obj.write_text(original_file_backup, encoding="utf-8")

    print("\n❌ Exhausted maximum healing attempts without passing all tests.")
    return False


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "target_app"
    heal_repository(target)