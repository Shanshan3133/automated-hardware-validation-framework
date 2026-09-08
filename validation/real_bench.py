"""Reference real-bench adapter.

This module intentionally does not energize equipment on import. Resource names,
channel scaling, current limits, and emergency-off behavior must be reviewed for
the specific lab before use.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from .instruments import Bench


class MCP3008:
    def __init__(self, cfg: dict):
        import spidev
        self.spi = spidev.SpiDev()
        self.spi.open(int(cfg["spi_bus"]), int(cfg["spi_device"]))
        self.spi.max_speed_hz = int(cfg.get("spi_hz", 1_000_000))
        self.vref = float(cfg["vref_v"])
        self.channels = cfg["channels"]

    def read_voltage(self, name: str) -> float:
        cfg = self.channels[name]
        channel = int(cfg["channel"])
        raw = self.spi.xfer2([1, (8 + channel) << 4, 0])
        code = ((raw[1] & 3) << 8) | raw[2]
        adc_v = code * self.vref / 1023.0
        return adc_v * float(cfg.get("divider_ratio", 1.0)) + float(cfg.get("offset_v", 0.0))

    def capture(self, name: str, sample_count: int, sample_rate_hz: int) -> list[float]:
        period = 1.0 / sample_rate_hz
        deadline = time.perf_counter()
        samples = []
        for _ in range(sample_count):
            samples.append(self.read_voltage(name))
            deadline += period
            remaining = deadline - time.perf_counter()
            if remaining > 0:
                time.sleep(remaining)
        return samples


class ActiveLowGPIO:
    def __init__(self, bcm_pin: int):
        import RPi.GPIO as GPIO
        self.GPIO, self.pin = GPIO, bcm_pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def read(self) -> bool:
        return bool(self.GPIO.input(self.pin))


class RealBench(Bench):
    def __init__(self, supply, load, adc, fault_gpio):
        self.supply, self.load, self.adc, self.fault_gpio = supply, load, adc, fault_gpio

    def set_input_voltage(self, volts: float) -> None:
        self.supply.write(f"VOLT {volts:.4f}")

    def set_load_current(self, amps: float) -> None:
        self.load.write(f"CURR {amps:.4f}")

    def output_on(self) -> None:
        self.supply.write("OUTP ON")
        self.load.write("INPUT ON")

    def output_off(self) -> None:
        self.load.write("INPUT OFF")
        self.supply.write("OUTP OFF")

    def measure_input_voltage(self) -> float:
        return float(self.supply.query("MEAS:VOLT?"))

    def measure_output_voltage(self) -> float:
        return float(self.adc.read_voltage("vout"))

    def measure_output_current(self) -> float:
        return float(self.load.query("MEAS:CURR?"))

    def acquire_output(self, sample_count: int, sample_rate_hz: int) -> list[float]:
        return self.adc.capture("vout", sample_count, sample_rate_hz)

    def fault_asserted(self) -> bool:
        return not bool(self.fault_gpio.read())  # DUT FLT is active-low


def build_real_bench(config_path: str | Path) -> RealBench:
    """Build a real bench only after applying conservative source limits."""
    cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
    current_limit = float(cfg["supply_current_limit_a"])
    if not 0 < current_limit <= 2.0:
        raise ValueError("supply_current_limit_a must be within (0, 2.0] A")
    import pyvisa
    manager = pyvisa.ResourceManager()
    supply = manager.open_resource(cfg["supply_resource"])
    load = manager.open_resource(cfg["load_resource"])
    supply.write("OUTP OFF")
    load.write("INPUT OFF")
    supply.write(f"CURR {current_limit:.4f}")
    supply.write(f"VOLT:PROT {float(cfg.get('supply_ovp_v', 22.0)):.4f}")
    return RealBench(supply, load, MCP3008(cfg["adc"]), ActiveLowGPIO(int(cfg["fault_gpio_bcm"])))
