import json
import tempfile
import unittest
from pathlib import Path

from validation.models import Status
from validation.report import write_results
from validation.real_bench import build_real_bench
from validation.simulator import SimulatedBench
from validation.test_cases import all_tests


class FrameworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads((Path(__file__).parents[1] / "validation" / "spec.json").read_text())

    def test_nominal_simulation_passes(self):
        with SimulatedBench(seed=7) as bench:
            results = all_tests(bench, self.spec)
        self.assertEqual(6, len(results))
        self.assertTrue(all(r.status == Status.PASS for r in results))

    def test_fault_injection_is_detected(self):
        with SimulatedBench(seed=7, fault="high-ripple") as bench:
            results = all_tests(bench, self.spec)
        ripple = next(r for r in results if r.name == "Output ripple")
        self.assertEqual(Status.FAIL, ripple.status)

    def test_report_artifacts(self):
        with SimulatedBench(seed=3) as bench:
            results = all_tests(bench, self.spec)
        with tempfile.TemporaryDirectory() as folder:
            report = write_results(Path(folder), results, {"dut": "unit-test"})
            self.assertTrue(report.exists())
            self.assertIn("Hardware Validation Report", report.read_text(encoding="utf-8"))
            self.assertTrue((Path(folder) / "results.json").exists())

    def test_real_bench_rejects_unsafe_current_limit_before_hardware_access(self):
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / "bench.json"
            config.write_text('{"supply_current_limit_a": 2.5}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "within"):
                build_real_bench(config)


if __name__ == "__main__":
    unittest.main()
