from __future__ import annotations

from abc import ABC, abstractmethod


class Bench(ABC):
    """Hardware abstraction consumed by all validation tests."""

    @abstractmethod
    def set_input_voltage(self, volts: float) -> None: ...

    @abstractmethod
    def set_load_current(self, amps: float) -> None: ...

    @abstractmethod
    def output_on(self) -> None: ...

    @abstractmethod
    def output_off(self) -> None: ...

    @abstractmethod
    def measure_input_voltage(self) -> float: ...

    @abstractmethod
    def measure_output_voltage(self) -> float: ...

    @abstractmethod
    def measure_output_current(self) -> float: ...

    @abstractmethod
    def acquire_output(self, sample_count: int, sample_rate_hz: int) -> list[float]: ...

    @abstractmethod
    def fault_asserted(self) -> bool: ...

    def safe_shutdown(self) -> None:
        self.set_load_current(0.0)
        self.output_off()

    def __enter__(self) -> "Bench":
        return self

    def __exit__(self, *_: object) -> None:
        self.safe_shutdown()

