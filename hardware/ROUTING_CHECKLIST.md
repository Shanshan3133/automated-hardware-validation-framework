# PCB Post-routing Review Checklist

The board now includes all footprints, named nets, a bottom ground plane, completed routing, test points, and the DAQ connector. KiCad 10.0.6 reports zero DRC violations and zero unconnected pads. The items below are engineering release gates, not missing ratsnest connections.

## Review in KiCad before fabrication

1. Minimize the U2–D2–L1–C8/C9 switching-current loops.
2. Confirm the R8/R9 Kelvin feedback path samples at the output capacitors and stays away from SW.
3. Confirm both ADC dividers, J3 pin order, and the 3.3 V maximum at every Raspberry Pi-facing signal.
4. Verify that TPS26600 RTN remains isolated from system GND through the intended device path.
5. Design and review the exposed-pad thermal-via arrays; check annular ring and drill limits with the selected manufacturer.
6. Add four M3 mounting holes and verify connector orientation and keep-outs against the enclosure.
7. Refill copper, rerun DRC, and preserve zero violations and zero unconnected items after every change.
8. Run schematic/PCB parity and inspect every autorouted neck-down, via, return path, and high-current segment manually.
9. Have another engineer review polarity, ratings, mode pins, protection behavior, creepage, and test-point access.

## Why this is not yet a fabrication release

Connectivity and automated rule checks are complete. TPS26600 configuration, TPS5431 compensation/bootstrap details, thermal-via design, land patterns, enclosure constraints, and final component derating still require review against the exact ordered parts.
