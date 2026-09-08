# Bring-up and bench safety

1. Inspect polarity, solder bridges, exposed pads, and connector pinout with power disconnected.
2. Check resistance from VIN to GND and VOUT to GND. Investigate unexpected low resistance.
3. Use a current-limited supply at 8 V and 100 mA with no load. Confirm no heating.
4. Raise the limit gradually, verify 5 V output, then test with a power resistor before connecting the automated fixture.
5. Configure the supply hardware OVP at 22 V and current limit at 2 A. Add a physical emergency-off that removes DUT power independently of Python.
6. Calibrate ADC channels against a traceable DMM. Record gain/offset and fixture revision.
7. Only then run threshold sweeps. Keep the first run attended and use thermal monitoring.

The low-cost ADC ripple result is a screening measurement, not a substitute for a bandwidth-limited oscilloscope measurement with a short ground spring.

