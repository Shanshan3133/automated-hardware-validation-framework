# Automated Hardware Validation Framework

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![KiCad](https://img.shields.io/badge/KiCad-10.0-314CB0?logo=kicad&logoColor=white)
![Tests](https://img.shields.io/badge/unit_tests-5%2F5_passing-16803C)
![Validation](https://img.shields.io/badge/simulated_validation-6%2F6_passing-16803C)
![Hardware](https://img.shields.io/badge/hardware-rev_A_in_progress-E2A000)

A portfolio project combining a protected 5 V buck-converter PCB with a Python automated validation bench. It demonstrates PCB design, instrument automation, fault injection, safety interlocks, data logging, and CI-style reporting—the day-to-day concerns of hardware validation and systems-integration engineering.

> **Engineering status:** the software framework is operational. The Rev-A PCB is a design in progress, not a fabrication release. KiCad reports zero geometric DRC violations, but 49 low-current connections still require interactive routing and schematic parity review. The higher count reflects the newly separated RTN/GND and protected DAQ networks.

## PCB preview

![Rev-A protected buck PCB 3D render](hardware/protected_buck_3d.png)

## Electrical architecture

![Protected 5 V buck schematic overview](docs/images/schematic_overview.svg)

This review overview explicitly separates the TPS26600 `RTN` domain from `SYSTEM_GND`, shows the required 10 nF BOOT-to-PH capacitor, and identifies the protected DAQ signals. The legacy editable schematic is still a concept artifact and must pass conversion and ERC before it can become the source of truth.

The DUT uses a TPS26600 eFuse front end and a TPS5431 asynchronous buck stage. It targets 8–18 V input, regulated 5 V output, and a 1 A continuous validation load. The fixture connector exposes divided VIN/VOUT measurements, active-low fault status, shutdown control, and current-monitor signals.

## System architecture

```mermaid
flowchart LR
    PY[Python test runner] -->|SCPI / USB| PSU[Programmable supply]
    PSU --> DUT[Protected 5 V buck DUT]
    DUT --> LOAD[Electronic load]
    DUT -->|VIN and VOUT| ADC[MCP3008 ADC]
    DUT -->|FLT and SHDN| GPIO[Raspberry Pi GPIO]
    ADC --> PI[Raspberry Pi]
    GPIO --> PI
    PI --> PY
    PY --> DATA[CSV and JSON results]
    DATA --> REPORT[CI-style HTML report]
```

All test logic depends on an abstract `Bench` interface. The same suite runs against a deterministic behavioral simulator in CI or against physical SCPI instruments and Raspberry Pi I/O in the lab.

## Automated test coverage

| Test | Stimulus | Measurement | Pass criterion |
|---|---|---|---|
| Line regulation | VIN from 8 V to 18 V | VOUT | 5.0 V ±3% |
| Load regulation | Load from 0 A to 1 A | VOUT | 5.0 V ±3% |
| Output ripple | 2,000 samples at 10 MS/s | Robust Vpp | <50 mVpp |
| UVLO rising | VIN from 6 V to 9 V | Turn-on threshold | 7.1–7.9 V |
| OVP rising | VIN from 17 V to 21 V | Fault threshold | 18.4–19.6 V |
| Overcurrent trip | Load from 0.5 A to 1.8 A | Fault threshold | 1.35–1.65 A |

The MCP3008 measures DC rails and low-frequency behavior. The physical ripple test deliberately requests a 10 MS/s window through a SCPI oscilloscope adapter because a low-speed ADC cannot characterize the TPS5431's 500 kHz switching ripple. Use a bandwidth-limited scope measurement with a short ground spring and verify the scope's actual acquisition settings.

## Example validation result

```text
PASS   Line regulation: VOUT range 4.995–5.011 V
PASS   Load regulation: VOUT range 4.992–5.010 V
PASS   Output ripple: Ripple 30.3 mVpp; mean 4.993 V
PASS   UVLO rising: Turn-on detected at 7.50 V
PASS   OVP rising: Trip detected at 19.05 V
PASS   Overcurrent trip: Trip detected at 1.500 A
```

View the self-contained [HTML report with measurement plots](artifacts/report.html), [machine-readable results](artifacts/results.json), and individual CSV files in `artifacts/`.

Fault injection verifies that real specification failures are detected:

```powershell
python -m validation.cli run --backend sim --fault high-ripple --output artifacts-failing
```

This produces a failing 91.3 mVpp result and a nonzero process exit code suitable for CI gating.

## Repository layout

```text
hardware/
  protected_buck.kicad_pro      KiCad project
  protected_buck.sch            legacy concept schematic; ERC cleanup pending
  protected_buck.kicad_pcb      Rev-A placement and critical power routing
  protected_buck_3d.png         generated 3D preview
  protected_buck_layout.pdf     top-layer preview
  BOM.csv                       preliminary bill of materials
  DESIGN.md                     calculations and layout rationale
  BRINGUP.md                    controlled first-power procedure
validation/
  instruments.py                bench abstraction
  simulator.py                  deterministic behavioral DUT model
  real_bench.py                 PyVISA supply/load/scope, MCP3008, and GPIO adapters
  test_cases.py                 validation procedures and limits
  report.py                     CSV, JSON, and HTML reporting
tests/                          software unit tests
scripts/generate_board.py       reproducible KiCad PCB generator
.github/workflows/              simulated validation workflow
```

## Quick start

Simulation requires Python 3.10+ and no third-party runtime packages:

```powershell
python -m validation.cli run --backend sim --output artifacts
python -m unittest discover -s tests -v
```

Open `artifacts/report.html` after the run.

## Physical bench setup

```powershell
pip install -e ".[raspberry-pi]"
Copy-Item validation/real_bench.example.json bench.json
python -m validation.cli run --backend real --config bench.json --output artifacts-real
```

Before using the real backend:

1. Verify SCPI resource names and commands against the exact instruments.
2. Calibrate every ADC divider and verify the oscilloscope probe ratio, bandwidth limit, and channel.
3. Install an independent physical emergency-off.
4. Configure the supply limit to 2 A or less and OVP to 22 V.
5. Complete [BRINGUP.md](hardware/BRINGUP.md) with the first run attended.

The real-bench factory rejects configurations above the 2 A project safety ceiling before opening hardware resources. `safe_shutdown()` removes the electronic load and source output if a test raises an exception.

## Hardware design targets

| Characteristic | Target |
|---|---:|
| Operating input range | 8–18 V |
| Output voltage | 5.0 V ±3% |
| Validation load | 1.0 A continuous |
| Automated ripple screen | <50 mVpp |
| UVLO rising threshold | 7.5 V ±0.4 V |
| OVP rising threshold | 19.0 V ±0.6 V |
| Current-limit trip | 1.50 A ±0.15 A |

See [DESIGN.md](hardware/DESIGN.md) for calculations, [VALIDATION_STATUS.md](hardware/VALIDATION_STATUS.md) for the exact engineering status, and [ROUTING_CHECKLIST.md](hardware/ROUTING_CHECKLIST.md) for remaining PCB work.

## Before fabrication

- Convert and clean the schematic in KiCad 10, then pass ERC.
- Route every remaining net and achieve zero DRC violations and zero unconnected items.
- Verify exposed-pad thermal-via patterns with the PCB manufacturer.
- Recheck compensation, bootstrap, current-limit mode, component derating, and fault behavior against the ordered part numbers.
- Run schematic/PCB parity checks and complete an independent engineering review.

This repository is an engineering portfolio artifact and learning platform. It is not a certified power product or production manufacturing release.
