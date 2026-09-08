from __future__ import annotations

import math
import random

from .instruments import Bench


class SimulatedBench(Bench):
    """Deterministic behavioral model used for development and CI."""

    def __init__(self, seed: int = 7, fault: str | None = None):
        self.rng = random.Random(seed)
        self.fault = fault
        self.vin_set = 0.0
        self.load_set = 0.0
        self.enabled = False
        self.uvlo = 7.48
        self.ovp = 19.05
        self.ilim = 1.50

    def set_input_voltage(self, volts: float) -> None:
        self.vin_set = max(0.0, volts)

    def set_load_current(self, amps: float) -> None:
        self.load_set = max(0.0, amps)

    def output_on(self) -> None:
        self.enabled = True

    def output_off(self) -> None:
        self.enabled = False

    def _tripped(self) -> bool:
        return (not self.enabled or self.vin_set < self.uvlo or
                self.vin_set >= self.ovp or self.load_set >= self.ilim)

    def measure_input_voltage(self) -> float:
        return self.vin_set + self.rng.gauss(0, 0.002)

    def measure_output_voltage(self) -> float:
        if self._tripped():
            return max(0.0, self.rng.gauss(0.012, 0.003))
        load_droop = 0.018 * self.load_set
        line_term = 0.0015 * (self.vin_set - 12.0)
        value = 5.01 + line_term - load_droop
        if self.fault == "bad-regulation":
            value += 0.22
        return value + self.rng.gauss(0, 0.0015)

    def measure_output_current(self) -> float:
        return 0.0 if self._tripped() else self.load_set + self.rng.gauss(0, 0.001)

    def acquire_output(self, sample_count: int, sample_rate_hz: int) -> list[float]:
        center = self.measure_output_voltage()
        amplitude = 0.014 if self.fault != "high-ripple" else 0.045
        switching_hz = 500_000.0
        return [center + amplitude * math.sin(2 * math.pi * switching_hz * i / sample_rate_hz)
                + self.rng.gauss(0, 0.001) for i in range(sample_count)]

    def fault_asserted(self) -> bool:
        return self.enabled and (self.vin_set < self.uvlo or self.vin_set >= self.ovp or
                                 self.load_set >= self.ilim)
