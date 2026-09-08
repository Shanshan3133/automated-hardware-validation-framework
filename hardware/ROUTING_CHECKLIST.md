# PCB Completion Checklist

The Rev-A board includes the major footprints, named nets, a system-ground plane, the critical power path, test points, and the DAQ connector. The latest generated DRC report is the source of truth for geometric violations and unconnected items.

## Complete in KiCad

1. Minimize the U2–D2–L1–C8/C9 switching-current loops.
2. Route BOOT, VSENSE, UVLO, OVP, ILIM, DVDT, FLT_DAQ, SHDN, MODE, and IMON_DAQ.
3. Kelvin-connect the R8/R9 feedback divider at the output capacitor rather than the inductor pad.
4. Route both ADC dividers and J3; confirm no J3 signal can exceed the Raspberry Pi 3.3 V input range.
5. Keep TPS26600 RTN isolated from system GND, add the correct thermal connections beneath both exposed pads, and check the manufacturer's minimum drill size.
6. Add four M3 mounting holes and verify connector orientation against the enclosure.
7. Refill copper and achieve both zero DRC violations and zero unconnected items.
8. Update the PCB from the converted schematic and run schematic/PCB parity checks.
9. Have another engineer review polarity, ratings, mode pins, protection behavior, and test-point access.

## Why this revision must not be fabricated yet

The critical power path is only a layout starting point and the low-current nets remain in the ratsnest. TPS26600 mode configuration, TPS5431 compensation/bootstrap details, thermal-via design, and final component derating must also be checked against the exact ordered parts.
