"""Minimal test runner, executed in a subprocess: python _testrunner.py <workspace> <test_file>.

Prints one line per test and a summary line. Kept dependency-free so it runs anywhere.
"""
import sys
import traceback
from pathlib import Path


def main() -> int:
    workspace, test_file = Path(sys.argv[1]), Path(sys.argv[2])
    sys.path.insert(0, str(workspace / "src"))
    namespace: dict = {"__name__": "tests_under_run"}
    try:
        code = compile(test_file.read_text(), str(test_file), "exec")
        exec(code, namespace)
    except Exception as exc:  # collection error
        print(f"ERROR collecting {test_file.name}: {type(exc).__name__}: {exc}")
        print("0 passed, 0 failed, 1 error")
        return 1

    tests = [(n, f) for n, f in namespace.items() if n.startswith("test_") and callable(f)]
    passed = failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASSED {name}")
            passed += 1
        except AssertionError as exc:
            print(f"FAILED {name} - {exc or 'assertion failed'}")
            failed += 1
        except Exception as exc:
            last = traceback.format_exception_only(type(exc), exc)[-1].strip()
            print(f"FAILED {name} - {last}")
            failed += 1
    print(f"{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
