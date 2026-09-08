"""Generate the Rev-A KiCad PCB using KiCad's bundled pcbnew API.

Run with KiCad's Python, for example:
  "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" scripts/generate_board.py
"""
from __future__ import annotations

import os
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware" / "protected_buck.kicad_pcb"
FP_ROOT = Path(os.environ.get("KICAD10_FOOTPRINT_DIR", r"C:\Program Files\KiCad\10.0\share\kicad\footprints"))
MM = pcbnew.FromMM


def vec(x: float, y: float):
    return pcbnew.VECTOR2I(MM(x), MM(y))


board = pcbnew.BOARD()
board.GetDesignSettings().SetAuxOrigin(vec(20, 40))
nets: dict[str, pcbnew.NETINFO_ITEM] = {}
for name in ["VIN", "GND", "PROTECTED_IN", "+5V", "SW", "BOOT", "UVLO", "OVP", "SHDN",
             "ILIM", "DVDT", "FLT", "VSENSE", "VIN_SENSE", "VOUT_SENSE", "IMON"]:
    net = pcbnew.NETINFO_ITEM(board, name)
    board.Add(net)
    nets[name] = net


def add_fp(lib: str, name: str, ref: str, value: str, x: float, y: float, rotation=0):
    fp = pcbnew.FootprintLoad(str(FP_ROOT / f"{lib}.pretty"), name)
    if fp is None:
        raise RuntimeError(f"Footprint not found: {lib}:{name}")
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPosition(vec(x, y))
    fp.SetOrientationDegrees(rotation)
    board.Add(fp)
    return fp


def assign(fp, mapping: dict[str, str]):
    for pad_number, net_name in mapping.items():
        matches = [pad for pad in fp.Pads() if pad.GetNumber() == pad_number]
        if not matches:
            raise RuntimeError(f"{fp.GetReference()} missing pad {pad_number}")
        for pad in matches:
            pad.SetNet(nets[net_name])


def resistor(ref, value, x, y, n1, n2, rotation=0):
    fp = add_fp("Resistor_SMD", "R_0603_1608Metric", ref, value, x, y, rotation)
    assign(fp, {"1": n1, "2": n2})
    return fp


def capacitor(ref, value, x, y, n1, n2, size="C_0603_1608Metric", rotation=0):
    fp = add_fp("Capacitor_SMD", size, ref, value, x, y, rotation)
    assign(fp, {"1": n1, "2": n2})
    return fp


J1 = add_fp("TerminalBlock_Phoenix", "TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal", "J1", "VIN 8-18V", 27, 65, 90)
assign(J1, {"1": "VIN", "2": "GND"})
D1 = add_fp("Diode_SMD", "D_SMB", "D1", "SMBJ24A", 36, 78, 90); assign(D1, {"1": "GND", "2": "VIN"})
C1 = capacitor("C1", "10uF 50V", 42, 75, "VIN", "GND", "C_1210_3225Metric", 90)
C2 = capacitor("C2", "10uF 50V", 46, 75, "VIN", "GND", "C_1210_3225Metric", 90)
C2.Reference().SetVisible(False)
U1 = add_fp("Package_SO", "HTSSOP-16-1EP_4.4x5mm_P0.65mm_EP3.4x5mm_Mask2.66x2.46mm", "U1", "TPS26600PWP", 56, 65)
assign(U1, {"1":"VIN", "2":"VIN", "3":"UVLO", "5":"OVP", "6":"GND", "7":"SHDN", "8":"GND", "9":"GND",
            "10":"IMON", "11":"ILIM", "12":"DVDT", "14":"FLT", "15":"PROTECTED_IN", "16":"PROTECTED_IN", "17":"GND"})
R1 = resistor("R1", "52.3k 1%", 47, 88, "VIN", "UVLO")
R2 = resistor("R2", "10k 1%", 52, 88, "UVLO", "GND")
R3 = resistor("R3", "150k 1%", 47, 92, "VIN", "OVP")
R4 = resistor("R4", "10k 1%", 52, 92, "OVP", "GND")
R5 = resistor("R5", "8.06k 1%", 63, 87, "ILIM", "GND")
C5 = capacitor("C5", "22nF", 67, 87, "DVDT", "GND")
R6 = resistor("R6", "10k", 68, 73, "PROTECTED_IN", "FLT", 90)
R7 = resistor("R7", "100k", 72, 73, "PROTECTED_IN", "SHDN", 90)
C6 = capacitor("C6", "10uF 50V", 76, 77, "PROTECTED_IN", "GND", "C_1210_3225Metric", 90)
U2 = add_fp("Package_SO", "TI_SO-PowerPAD-8", "U2", "TPS5431DDA", 86, 65)
assign(U2, {"1":"BOOT", "4":"VSENSE", "5":"PROTECTED_IN", "6":"GND", "7":"PROTECTED_IN", "8":"SW", "9":"GND"})
C7 = capacitor("C7", "10nF BOOT", 91, 57, "BOOT", "SW")
D2 = add_fp("Diode_SMD", "D_SMA", "D2", "B340A", 95, 76, 90); assign(D2, {"1":"GND", "2":"SW"})
L1 = add_fp("Inductor_SMD", "L_10.4x10.4_H4.8", "L1", "15uH 4A", 103, 65); assign(L1, {"1":"SW", "2":"+5V"})
C8 = capacitor("C8", "47uF 10V", 115, 76, "+5V", "GND", "C_1210_3225Metric", 90)
C9 = capacitor("C9", "47uF 10V", 120, 76, "+5V", "GND", "C_1210_3225Metric", 90)
R8 = resistor("R8", "30.9k 1%", 93, 90, "+5V", "VSENSE")
R9 = resistor("R9", "10k 1%", 99, 90, "VSENSE", "GND")
J2 = add_fp("TerminalBlock_Phoenix", "TerminalBlock_Phoenix_MKDS-1,5-2_1x02_P5.00mm_Horizontal", "J2", "5V OUT", 133, 65, 90)
assign(J2, {"1":"+5V", "2":"GND"})

# DAQ divider/interface section.
R10 = resistor("R10", "56k 1%", 105, 95, "VIN", "VIN_SENSE")
R11 = resistor("R11", "10k 1%", 111, 95, "VIN_SENSE", "GND")
R12 = resistor("R12", "10k 1%", 105, 100, "+5V", "VOUT_SENSE")
R13 = resistor("R13", "15k 1%", 111, 100, "VOUT_SENSE", "GND")
J3 = add_fp("Connector_PinHeader_2.54mm", "PinHeader_1x06_P2.54mm_Vertical", "J3", "DAQ", 125, 96, 90)
assign(J3, {"1":"GND", "2":"VIN_SENSE", "3":"VOUT_SENSE", "4":"FLT", "5":"SHDN", "6":"IMON"})

for ref, x, y, net in [("TP1",35,47,"VIN"), ("TP2",70,47,"PROTECTED_IN"), ("TP3",113,47,"+5V"), ("TP4",125,47,"GND")]:
    tp = add_fp("TestPoint", "TestPoint_Plated_Hole_D2.0mm", ref, net, x, y)
    assign(tp, {"1":net})


def track(net_name: str, width: float, *points: tuple[float, float]):
    for a, b in zip(points, points[1:]):
        seg = pcbnew.PCB_TRACK(board)
        seg.SetNet(nets[net_name]); seg.SetLayer(pcbnew.F_Cu); seg.SetWidth(MM(width))
        seg.SetStart(vec(*a)); seg.SetEnd(vec(*b)); board.Add(seg)


def padxy(fp, num):
    p = fp.FindPadByNumber(str(num)).GetPosition()
    return pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)


# Critical high-current path is pre-routed. Low-current/protection nets remain as a
# visible ratsnest for final interactive routing and design review in KiCad.
track("VIN",0.8,padxy(J1,1),(40,65),(49,60),padxy(U1,1))
track("VIN",0.3,padxy(U1,1),padxy(U1,2))
track("PROTECTED_IN",0.3,padxy(U1,15),padxy(U1,16))
track("PROTECTED_IN",0.8,padxy(U1,16),(61.5,62.725),(61.5,70),(92,70),(92,64.365),padxy(U2,7))
track("PROTECTED_IN",0.3,padxy(U2,7),(91,64.365),(91,66.905),padxy(U2,5))
track("SW",0.6,padxy(U2,8),(94,63.095),padxy(L1,1))
track("+5V",1.2,padxy(L1,2),(120,65),(130,65),padxy(J2,1))

# Board outline.
for a, b in [((20,40),(140,40)),((140,40),(140,110)),((140,110),(20,110)),((20,110),(20,40))]:
    edge = pcbnew.PCB_SHAPE(board); edge.SetShape(pcbnew.SHAPE_T_SEGMENT); edge.SetLayer(pcbnew.Edge_Cuts)
    edge.SetStart(vec(*a)); edge.SetEnd(vec(*b)); edge.SetWidth(MM(0.25)); board.Add(edge)

# Ground plane, filled during generation.
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    zone = pcbnew.ZONE(board); zone.SetLayer(layer); zone.SetNet(nets["GND"]); zone.SetLocalClearance(MM(0.3))
    outline = zone.Outline(); outline.NewOutline()
    for p in [(20.5,40.5),(139.5,40.5),(139.5,109.5),(20.5,109.5)]: outline.Append(*vec(*p))
    board.Add(zone)

label = pcbnew.PCB_TEXT(board); label.SetText("PROTECTED 5V BUCK | REV A"); label.SetLayer(pcbnew.F_SilkS)
label.SetPosition(vec(80,43)); label.SetTextSize(vec(1.5,1.5)); label.SetTextThickness(MM(0.3)); board.Add(label)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(OUT), board)
print(f"Generated {OUT}")
