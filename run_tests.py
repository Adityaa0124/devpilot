"""
DevPilot Automated Test Runner.
Executes all unit and regression test modules, capturing detailed results,
assertions, and summary execution metrics without external plugin hangs.
"""

import sys
import time
import inspect
import importlib

TEST_MODULES = [
    "tests.test_secure_execution",
    "tests.test_security_reviewer",
    "tests.test_test_generator",
    "tests.test_workflow_routing",
    "tests.test_llm_provider",
    "tests.test_planner",
    "tests.test_developer",
    "tests.test_reviewer",
    "tests.test_blind_subagents",
    "tests.test_evaluator",
]


def run_all_tests():
    total_run = 0
    passed = 0
    failed = 0
    failures = []

    print("=" * 80)
    print("           DEVPILOT TEST SUITE — EXECUTION & VERIFICATION")
    print("=" * 80)

    start_suite = time.time()

    for mod_name in TEST_MODULES:
        print(f"\n📂 Module: {mod_name}")
        try:
            mod = importlib.import_module(mod_name)
        except Exception as exc:
            print(f"  ❌ FAILED TO IMPORT {mod_name}: {exc}")
            failed += 1
            failures.append((mod_name, "import", str(exc)))
            continue

        test_funcs = [
            (name, func) for name, func in inspect.getmembers(mod, inspect.isfunction)
            if name.startswith("test_")
        ]

        for name, func in test_funcs:
            total_run += 1
            t0 = time.time()
            try:
                func()
                elapsed_ms = round((time.time() - t0) * 1000)
                print(f"  ✓ {name} ({elapsed_ms}ms)")
                passed += 1
            except Exception as exc:
                elapsed_ms = round((time.time() - t0) * 1000)
                print(f"  ✗ {name} ({elapsed_ms}ms) -> {exc}")
                failed += 1
                failures.append((mod_name, name, str(exc)))

    total_time = round(time.time() - start_suite, 2)

    print("\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed (Total: {total_run}) in {total_time}s")
    print("=" * 80)

    if failures:
        print("\nFAILURE DETAILS:")
        for mod, name, err in failures:
            print(f"  - [{mod}] {name}: {err}")
        return 1

    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")
    return 0


if __name__ == "__main__":
    sys.exit(run_all_tests())

