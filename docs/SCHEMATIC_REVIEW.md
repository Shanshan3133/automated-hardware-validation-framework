# Schematic review notes

This revision converts the most important observations from the KiCad review into explicit design constraints. The README now includes both the clean architecture diagram and the exported KiCad schematic. The editable native schematic passes ERC with zero errors and zero warnings.

## Corrected constraints

- Keep TPS26600 `RTN` separate from downstream `SYSTEM_GND`; do not replace the internal reverse-polarity path with a copper short.
- Reference UVLO, OVP, ILIM, dV/dt, MODE, and IMON programming components to `RTN`.
- Fit 10 nF from TPS5431 BOOT to PH/SW and place it at the IC pins.
- Use a 0 Ω MODE-to-RTN option for active current-limit auto-retry.
- Provide the FLT pull-up in the 3.3 V fixture domain; never pull a Raspberry Pi input to the protected power rail.
- Drive SHDN through an open-drain or isolated fixture output.
- Use the oscilloscope backend for ripple; do not claim 500 kHz ripple performance from a 10 kS/s ADC.

## Release gate

The KiCad source remains an engineering prototype. ERC, DRC, and connectivity gates are clean. Before fabrication, verify land patterns and exact ordered parts, complete schematic/PCB parity, review thermal and mechanical design, and obtain an independent engineering review.
