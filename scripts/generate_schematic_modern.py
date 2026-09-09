"""Build the complete KiCad 10 schematic from verified symbol templates."""
from __future__ import annotations

import re
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "hardware" / "protected_buck.kicad_sch"
OUTPUT = ROOT / "hardware" / "protected_buck.kicad_sch"
MM = 0.0254


def balanced(text: str, start: int) -> str:
    depth = 0
    quoted = False
    escaped = False
    for pos in range(start, len(text)):
        ch = text[pos]
        if quoted:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                quoted = False
        elif ch == '"':
            quoted = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[start:pos + 1]
    raise ValueError("Unbalanced KiCad expression")


def top_blocks(text: str, token: str) -> list[str]:
    blocks: list[str] = []
    depth = 0
    quoted = False
    escaped = False
    i = 0
    while i < len(text):
        ch = text[i]
        if quoted:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                quoted = False
        elif ch == '"':
            quoted = True
        elif ch == "(":
            if depth == 1 and text.startswith(token, i):
                block = balanced(text, i)
                blocks.append(block)
                i += len(block)
                continue
            depth += 1
        elif ch == ")":
            depth -= 1
        i += 1
    return blocks


source = SOURCE.read_text(encoding="utf-8")
lib_start = source.index("\t(lib_symbols")
lib_block = balanced(source, lib_start)
if '(symbol "power:PWR_FLAG"' not in lib_block:
    power_lib = Path(r"C:\Program Files\KiCad\10.0\share\kicad\symbols\power.kicad_sym").read_text(encoding="utf-8")
    flag_start = power_lib.index('\t(symbol "PWR_FLAG"')
    flag_symbol = balanced(power_lib, flag_start)
    flag_symbol = flag_symbol.replace('(symbol "PWR_FLAG"', '(symbol "power:PWR_FLAG"', 1)
    lib_block = lib_block[:-1] + "\n" + flag_symbol + "\n\t)"
header = source[:lib_start]
header = re.sub(r'\(date "[^"]*"\)', '(date "2026-09-09")', header, count=1)
header = re.sub(r'\(rev "[^"]*"\)', '(rev "B")', header, count=1)
symbol_blocks = top_blocks(source, "(symbol\n")
templates: dict[str, str] = {}
for block in symbol_blocks:
    match = re.search(r'\(property "Reference" "([^"]+)"', block)
    if match:
        templates[match.group(1)] = block


def translated_symbol(template_ref: str, ref: str, value: str, footprint: str,
                      x_mil: int, y_mil: int) -> str:
    block = templates[template_ref]
    at = re.search(r'\(at ([\d.]+) ([\d.]+) (\d+)\)', block)
    if not at:
        raise ValueError(f"No position in template {template_ref}")
    old_x, old_y = float(at.group(1)), float(at.group(2))
    new_x, new_y = x_mil * MM, y_mil * MM
    dx, dy = new_x - old_x, new_y - old_y

    def move(match: re.Match[str]) -> str:
        x = float(match.group(1)) + dx
        y = float(match.group(2)) + dy
        rest = match.group(3)
        return f"(at {x:.4f} {y:.4f}{rest})"

    block = re.sub(r'\(at (-?[\d.]+) (-?[\d.]+)([^)]*)\)', move, block)
    block = re.sub(r'(\(property "Reference" ")[^"]+', rf'\g<1>{ref}', block, count=1)
    block = re.sub(r'(\(property "Value" ")[^"]+', rf'\g<1>{value}', block, count=1)
    block = re.sub(r'(\(property "Footprint" ")[^"]*', rf'\g<1>{footprint}', block, count=1)
    block = re.sub(r'(\(reference ")[^"]+', rf'\g<1>{ref}', block)
    if ref.startswith("#FLG"):
        block = block.replace('(lib_id "power:GND")', '(lib_id "power:PWR_FLAG")', 1)
    block = re.sub(r'\(uuid "[0-9a-f-]+"\)', lambda _: f'(uuid "{uuid.uuid4()}")', block)
    return "\t" + block.replace("\n", "\n\t")


parts = [
    ("J1", "J1", "VIN_8-18V", "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal", 1050, 2500),
    ("D1", "D1", "SMBJ24A", "Diode_SMD:D_SMB", 1600, 2850),
    ("C1", "C1", "10uF 50V", "Capacitor_SMD:C_1210_3225Metric", 1950, 2850),
    ("C1", "C2", "10uF 50V", "Capacitor_SMD:C_1210_3225Metric", 2300, 2850),
    ("U1", "U1", "TPS26600PWP", "Package_SO:HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3.4x5mm_Mask2.66x2.46mm", 3500, 3000),
    ("R1", "R1", "52.3k 1%", "Resistor_SMD:R_0603_1608Metric", 2350, 3900),
    ("R1", "R2", "10k 1%", "Resistor_SMD:R_0603_1608Metric", 2350, 4400),
    ("R1", "R3", "150k 1%", "Resistor_SMD:R_0603_1608Metric", 3300, 4300),
    ("R1", "R4", "10k 1%", "Resistor_SMD:R_0603_1608Metric", 3300, 4800),
    ("R1", "R5", "8.06k 1%", "Resistor_SMD:R_0603_1608Metric", 4300, 3900),
    ("C1", "C5", "22nF", "Capacitor_SMD:C_0603_1608Metric", 4700, 3900),
    ("R1", "R6", "1k", "Resistor_SMD:R_0603_1608Metric", 5100, 3900),
    ("R1", "R7", "100k", "Resistor_SMD:R_0603_1608Metric", 5500, 3900),
    ("R1", "R14", "0R", "Resistor_SMD:R_0603_1608Metric", 3900, 4500),
    ("R1", "R15", "16.9k 1%", "Resistor_SMD:R_0603_1608Metric", 4400, 4500),
    ("R1", "R16", "100k", "Resistor_SMD:R_0603_1608Metric", 5000, 4500),
    ("C1", "C6", "10uF 50V", "Capacitor_SMD:C_1210_3225Metric", 5700, 3300),
    ("U2", "U2", "TPS5431DDA", "Package_SO:TI_SO-PowerPAD-8", 6500, 2800),
    ("C1", "C7", "10nF BOOT", "Capacitor_SMD:C_0603_1608Metric", 7200, 2400),
    ("D2", "D2", "B340A", "Diode_SMD:D_SMA", 7200, 3300),
    ("L1", "L1", "15uH 4A", "Inductor_SMD:L_10.4x10.4_H4.8", 7600, 2800),
    ("C1", "C8", "47uF 10V", "Capacitor_SMD:C_1210_3225Metric", 8050, 3300),
    ("C1", "C9", "47uF 10V", "Capacitor_SMD:C_1210_3225Metric", 8400, 3300),
    ("R1", "R8", "30.9k 1%", "Resistor_SMD:R_0603_1608Metric", 8050, 4000),
    ("R1", "R9", "10k 1%", "Resistor_SMD:R_0603_1608Metric", 8050, 4500),
    ("J2", "J2", "5V_OUT", "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal", 9100, 2800),
    ("R1", "R10", "56k 1%", "Resistor_SMD:R_0603_1608Metric", 6500, 4300),
    ("R1", "R11", "10k 1%", "Resistor_SMD:R_0603_1608Metric", 6500, 4800),
    ("R1", "R12", "10k 1%", "Resistor_SMD:R_0603_1608Metric", 7200, 4300),
    ("R1", "R13", "15k 1%", "Resistor_SMD:R_0603_1608Metric", 7200, 4800),
    ("J3", "J3", "DAQ", "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical", 9400, 5000),
]
flag_template = "#PWR01" if "#PWR01" in templates else "#FLG0101"
parts.extend([
    (flag_template, "#FLG0101", "PWR_FLAG", "", 1350, 2300),
    (flag_template, "#FLG0102", "PWR_FLAG", "", 1350, 4700),
])

points: dict[str, list[tuple[int, int]]] = {}


def net(name: str, x: int, y: int) -> None:
    points.setdefault(name, []).append((x, y))


for name, x, y in [("VIN",1250,2500),("RTN",1250,2600),("RTN",1600,2700),("VIN",1600,3000),
                    ("VIN",1950,2700),("RTN",1950,3000),("VIN",2300,2700),("RTN",2300,3000)]: net(name,x,y)
for item in [("VIN",3000,2500),("UVLO",3000,2800),("OVP",3000,3100),("MODE",3000,3400),
             ("SHDN",3000,3500),("RTN",3400,3700),("GND",3600,3700),("PROTECTED_IN",4000,2500),
             ("FLT",4000,3000),("IMON",4000,3100),("ILIM",4000,3400),("DVDT",4000,3500)]: net(*item)
for name,x,y in [("VIN",2350,3750),("UVLO",2350,4050),("UVLO",2350,4250),("RTN",2350,4550),
                 ("VIN",3300,4150),("OVP",3300,4450),("OVP",3300,4650),("RTN",3300,4950),
                 ("ILIM",4300,3750),("RTN",4300,4050),("DVDT",4700,3750),("RTN",4700,4050),
                 ("FLT",5100,3750),("FLT_DAQ",5100,4050),("PROTECTED_IN",5500,3750),("SHDN",5500,4050),
                 ("MODE",3900,4350),("RTN",3900,4650),("IMON",4400,4350),("RTN",4400,4650),
                 ("IMON",5000,4350),("IMON_DAQ",5000,4650),("PROTECTED_IN",5700,3150),("GND",5700,3450)]: net(name,x,y)
for item in [("PROTECTED_IN",6000,2600),("PROTECTED_IN",6000,3000),("GND",6400,3200),("GND",6500,3200),
             ("BOOT",7000,2600),("SW",7000,2800),("VSENSE",7000,3000),("BOOT",7200,2250),("SW",7200,2550),
             ("GND",7200,3150),("SW",7200,3450),("SW",7450,2800),("+5V",7750,2800)]: net(*item)
for name,x,y in [("+5V",8050,3150),("GND",8050,3450),("+5V",8400,3150),("GND",8400,3450),
                 ("+5V",8050,3850),("VSENSE",8050,4150),("VSENSE",8050,4350),("GND",8050,4650),
                 ("+5V",8900,2800),("GND",8900,2900),("VIN",6500,4150),("VIN_SENSE",6500,4450),
                 ("VIN_SENSE",6500,4650),("GND",6500,4950),("+5V",7200,4150),("VOUT_SENSE",7200,4450),
                 ("VOUT_SENSE",7200,4650),("GND",7200,4950)]: net(name,x,y)
for name,y in [("GND",4800),("VIN_SENSE",4900),("VOUT_SENSE",5000),("FLT_DAQ",5100),("SHDN",5200),("IMON_DAQ",5300)]: net(name,9200,y)
net("VIN", 1350, 2300)
net("GND", 1350, 4700)


def wire_label(name: str, x_mil: int, y_mil: int, index: int) -> str:
    x, y = x_mil * MM, y_mil * MM
    end_x = x + 2.54
    return f'''\t(wire
\t\t(pts (xy {x:.4f} {y:.4f}) (xy {end_x:.4f} {y:.4f}))
\t\t(stroke (width 0) (type default))
\t\t(uuid "{uuid.uuid4()}")
\t)
\t(label "{name}"
\t\t(at {end_x:.4f} {y:.4f} 0)
\t\t(effects (font (size 1.27 1.27)) (justify left bottom))
\t\t(uuid "{uuid.uuid4()}")
\t)
'''


objects: list[str] = []
for name, coords in points.items():
    for index, (x, y) in enumerate(coords):
        objects.append(wire_label(name, x, y, index))
for spec in parts:
    objects.append(translated_symbol(*spec))

tail = '''\t(sheet_instances
\t\t(path "/" (page "1"))
\t)
\t(embedded_fonts no)
)\n'''
OUTPUT.write_text(header + lib_block + "\n" + "".join(objects) + tail, encoding="utf-8")
print(f"Generated {OUTPUT}")
