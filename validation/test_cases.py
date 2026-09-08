from __future__ import annotations

import statistics
import time
from collections.abc import Callable

from .instruments import Bench
from .models import Measurement, Status, TestResult


def _points(start: float, stop: float, step: float) -> list[float]:
    count = round((stop - start) / step)
    return [round(start + i * step, 6) for i in range(count + 1)]


def line_regulation(bench: Bench, spec: dict) -> TestResult:
    started = time.monotonic()
    low = spec["nominal_output_v"] * (1 - spec["output_tolerance_pct"] / 100)
    high = spec["nominal_output_v"] * (1 + spec["output_tolerance_pct"] / 100)
    rows = []
    bench.set_load_current(spec["rated_load_a"] * 0.5)
    bench.output_on()
    for vin in _points(*spec["operating_input_v"], 1.0):
        bench.set_input_voltage(vin)
        vout = bench.measure_output_voltage()
        rows.append(Measurement("line_regulation", vin, "V", vout, "V"))
    passed = all(low <= r.value <= high for r in rows)
    return TestResult("Line regulation", Status.PASS if passed else Status.FAIL,
                      f"VOUT range {min(r.value for r in rows):.3f}–{max(r.value for r in rows):.3f} V",
                      rows, {"min_v": low, "max_v": high}, time.monotonic() - started)


def load_regulation(bench: Bench, spec: dict) -> TestResult:
    started = time.monotonic()
    low = spec["nominal_output_v"] * (1 - spec["output_tolerance_pct"] / 100)
    high = spec["nominal_output_v"] * (1 + spec["output_tolerance_pct"] / 100)
    bench.set_input_voltage(12.0)
    bench.output_on()
    rows = []
    for load in _points(0.0, spec["rated_load_a"], 0.1):
        bench.set_load_current(load)
        rows.append(Measurement("load_regulation", load, "A", bench.measure_output_voltage(), "V"))
    passed = all(low <= r.value <= high for r in rows)
    return TestResult("Load regulation", Status.PASS if passed else Status.FAIL,
                      f"VOUT range {min(r.value for r in rows):.3f}–{max(r.value for r in rows):.3f} V",
                      rows, {"min_v": low, "max_v": high}, time.monotonic() - started)


def ripple(bench: Bench, spec: dict) -> TestResult:
    started = time.monotonic()
    bench.set_input_voltage(12.0)
    bench.set_load_current(spec["rated_load_a"])
    bench.output_on()
    samples = bench.acquire_output(spec["ripple_samples"], spec["ripple_sample_rate_hz"])
    ordered = sorted(samples)
    trim = max(1, len(ordered) // 100)
    robust_vpp = ordered[-trim] - ordered[trim - 1]
    limit = spec["ripple_limit_vpp"]
    rows = [Measurement("ripple", i / spec["ripple_sample_rate_hz"], "s", v, "V")
            for i, v in enumerate(samples)]
    return TestResult("Output ripple", Status.PASS if robust_vpp <= limit else Status.FAIL,
                      f"Ripple {robust_vpp * 1000:.1f} mVpp; mean {statistics.fmean(samples):.3f} V",
                      rows, {"max_vpp": limit}, time.monotonic() - started)


def _find_trip(bench: Bench, values: list[float], stimulus: str,
               set_value: Callable[[float], None], trips_when: Callable[[], bool]) -> tuple[float | None, list[Measurement]]:
    rows = []
    for value in values:
        set_value(value)
        vout = bench.measure_output_voltage()
        tripped = trips_when()
        rows.append(Measurement(stimulus, value, "V" if stimulus != "overcurrent" else "A", vout, "V",
                                "TRIP" if tripped else "ON"))
        if tripped:
            return value, rows
    return None, rows


def protection_thresholds(bench: Bench, spec: dict) -> list[TestResult]:
    results = []
    bench.set_load_current(0.25)
    bench.output_on()
    trip, rows = _find_trip(bench, _points(6.0, 9.0, 0.05), "uvlo", bench.set_input_voltage,
                            lambda: bench.measure_output_voltage() > 4.5)
    lo, hi = spec["uvlo_rising_v"]
    results.append(TestResult("UVLO rising", Status.PASS if trip is not None and lo <= trip <= hi else Status.FAIL,
                              f"Turn-on detected at {trip:.2f} V" if trip else "No turn-on detected", rows,
                              {"min_v": lo, "max_v": hi}))

    bench.set_load_current(0.25)
    trip, rows = _find_trip(bench, _points(17.0, 21.0, 0.05), "ovp", bench.set_input_voltage,
                            lambda: bench.fault_asserted())
    lo, hi = spec["ovp_rising_v"]
    results.append(TestResult("OVP rising", Status.PASS if trip is not None and lo <= trip <= hi else Status.FAIL,
                              f"Trip detected at {trip:.2f} V" if trip else "No trip detected", rows,
                              {"min_v": lo, "max_v": hi}))

    bench.set_input_voltage(12.0)
    trip, rows = _find_trip(bench, _points(0.5, 1.8, 0.025), "overcurrent", bench.set_load_current,
                            lambda: bench.fault_asserted())
    lo, hi = spec["current_trip_a"]
    results.append(TestResult("Overcurrent trip", Status.PASS if trip is not None and lo <= trip <= hi else Status.FAIL,
                              f"Trip detected at {trip:.3f} A" if trip else "No trip detected", rows,
                              {"min_a": lo, "max_a": hi}))
    return results


def all_tests(bench: Bench, spec: dict) -> list[TestResult]:
    return [line_regulation(bench, spec), load_regulation(bench, spec), ripple(bench, spec),
            *protection_thresholds(bench, spec)]

