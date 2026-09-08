# Protected buck design notes

## Power path

J1 feeds TVS D1 and TPS26600 eFuse U1. U1 provides reverse-polarity protection, adjustable UVLO/OVP, inrush control, current limiting, and an active-low fault output. Its protected output feeds TPS5431 U2, configured as a 5 V asynchronous buck using L1, D2, and C8/C9. J2 is the load output; J3 exposes divided VIN/VOUT sense, FLT, shutdown, current monitor, and ground to the Raspberry Pi fixture.

## First-pass calculations

TPS26600 adjustable UVLO/OVP comparators are nominally 1.19 V. Divider threshold is approximately `VTRIP = 1.19 × (RTOP + RBOT) / RBOT`.

- UVLO: 52.3 kΩ / 10 kΩ → 7.41 V nominal.
- OVP: 150 kΩ / 10 kΩ → 19.04 V nominal.
- ILIM: 8.06 kΩ corresponds to approximately 1.5 A from the datasheet characterization.
- TPS5431 feedback: 1.221 V reference with 30.9 kΩ / 10 kΩ → 4.99 V nominal.

The 15 µH inductor and 2 × 47 µF output capacitance are starting values. Confirm loop stability, saturation margin, RMS ripple current, and thermal rise using the final capacitor bias curves and vendor design tools.

## Layout intent

- Keep U2–D2–L1 switching loop compact and on the top layer.
- Use a solid bottom ground plane and via-stitch both exposed pads.
- Kelvin-route FB from the output capacitor, away from SW.
- Place TVS and input ceramics at J1/U1; place output ceramics at L1/J2.
- Route DAQ sense traces separately from high-current copper and join at Kelvin points.

## Review gates before fabrication

1. Replace any generic footprints with verified manufacturer land patterns.
2. Run KiCad ERC/DRC and resolve every warning intentionally.
3. Verify TPS26600 MODE, dV/dt, TPS5431 bootstrap network, and both exposed-pad connections against the current datasheets.
4. Validate creepage, copper width, via current, component derating, and enclosure constraints.
5. Have another engineer review the schematic and layout.
