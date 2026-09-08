from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

from .models import Status, TestResult
from .report import write_results
from .simulator import SimulatedBench
from .test_cases import all_tests


def run(args: argparse.Namespace) -> int:
    spec_path = Path(__file__).with_name("spec.json")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if args.backend == "sim":
        bench = SimulatedBench(seed=args.seed, fault=args.fault)
    else:
        if not args.config:
            raise SystemExit("--config is required with --backend real")
        from .real_bench import build_real_bench
        bench = build_real_bench(args.config)
    results: list[TestResult] = []
    try:
        with bench:
            results = all_tests(bench, spec)
    except Exception as exc:
        results.append(TestResult("Bench execution", Status.ERROR, f"{type(exc).__name__}: {exc}"))
    metadata = {"dut": spec["dut_name"], "backend": args.backend, "seed": args.seed,
                "fault_injection": args.fault or "none", "host": platform.node(), "python": platform.python_version()}
    report = write_results(Path(args.output), results, metadata)
    for result in results:
        print(f"{result.status.value:5}  {result.name}: {result.summary}")
    print(f"Report: {report.resolve()}")
    return 0 if results and all(r.status == Status.PASS for r in results) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Automated protected-buck validation")
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("run")
    command.add_argument("--backend", choices=["sim", "real"], default="sim")
    command.add_argument("--output", default="artifacts")
    command.add_argument("--seed", type=int, default=7)
    command.add_argument("--fault", choices=["high-ripple", "bad-regulation"])
    command.add_argument("--config", help="Real-bench JSON configuration")
    command.set_defaults(func=run)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
