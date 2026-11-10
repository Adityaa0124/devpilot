import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from evals.evaluator import BenchmarkHarness

if __name__ == "__main__":
    harness = BenchmarkHarness()
    results = harness.run_benchmark()

    # Save to evals/results.json
    output_path = os.path.join(os.path.dirname(__file__), "results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n📁 Benchmark report successfully written to {output_path}")

