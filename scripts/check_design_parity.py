"""Compare schematic pin nets with PCB pad nets using KiCad 10."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
SCHEMATIC = ROOT / "hardware" / "protected_buck.kicad_sch"
BOARD = ROOT / "hardware" / "protected_buck.kicad_pcb"
KICAD_CLI = Path(sys.executable).with_name("kicad-cli.exe")


with tempfile.TemporaryDirectory(prefix="hardware-parity-") as folder:
    netlist = Path(folder) / "protected_buck.xml"
    subprocess.run(
        [str(KICAD_CLI), "sch", "export", "netlist", "--format", "kicadxml", "-o", str(netlist), str(SCHEMATIC)],
        check=True,
    )
    root = ET.parse(netlist).getroot()

schematic: dict[tuple[str, str], str] = {}
for net in root.findall("./nets/net"):
    net_name = net.attrib["name"].removeprefix("/")
    for node in net.findall("node"):
        ref = node.attrib["ref"]
        if not ref.startswith("#"):
            schematic[(ref, node.attrib["pin"])] = net_name

board = pcbnew.LoadBoard(str(BOARD))
pcb: dict[tuple[str, str], str] = {}
for footprint in board.GetFootprints():
    ref = footprint.GetReference()
    if ref.startswith("TP"):
        continue
    for pad in footprint.Pads():
        if pad.GetNumber():
            pcb[(ref, pad.GetNumber())] = pad.GetNetname()

problems: list[str] = []
for key in sorted(set(schematic) | set(pcb)):
    sch_net = schematic.get(key)
    pcb_net = pcb.get(key)
    if (sch_net or "").startswith("unconnected-") and not pcb_net:
        continue
    if sch_net != pcb_net:
        problems.append(f"{key[0]}.{key[1]}: schematic={sch_net!r}, pcb={pcb_net!r}")

if problems:
    print("Schematic/PCB parity failed:")
    print("\n".join(problems))
    raise SystemExit(1)

print(f"PASS: {len(schematic)} schematic pins match {len(pcb)} PCB pads")
