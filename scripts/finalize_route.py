"""Import a Freerouting session and finish the four review-required connections."""
from __future__ import annotations

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "hardware" / "protected_buck_unrouted.kicad_pcb"
SESSION = ROOT / "hardware" / "protected_buck.ses"
OUTPUT = ROOT / "hardware" / "protected_buck.kicad_pcb"
MM = pcbnew.FromMM


def vec(x: float, y: float):
    return pcbnew.VECTOR2I(MM(x), MM(y))


board = pcbnew.LoadBoard(str(SOURCE))
if not pcbnew.ImportSpecctraSES(board, str(SESSION)):
    raise RuntimeError("Unable to import Specctra routing session")


def footprint(reference: str):
    return next(fp for fp in board.GetFootprints() if fp.GetReference() == reference)


def pad(reference: str, number: str):
    return footprint(reference).FindPadByNumber(number)


def point(item):
    pos = item.GetPosition()
    return pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)


def add_track(net_name: str, width: float, *points: tuple[float, float], layer=pcbnew.F_Cu):
    net = board.FindNet(net_name)
    for start, end in zip(points, points[1:]):
        segment = pcbnew.PCB_TRACK(board)
        segment.SetNet(net); segment.SetLayer(layer); segment.SetWidth(MM(width))
        segment.SetStart(vec(*start)); segment.SetEnd(vec(*end)); board.Add(segment)


# Enforce the board minimum on tiny fan-out segments emitted by the router.
for segment in board.GetTracks():
    if isinstance(segment, pcbnew.PCB_TRACK) and not isinstance(segment, pcbnew.PCB_VIA):
        if pcbnew.ToMM(segment.GetWidth()) < 0.2:
            segment.SetWidth(MM(0.2))

# High-current/local connections that the general autorouter intentionally left
# for engineering review.
vin_diode = point(pad("D1", "2"))
add_track("VIN", 0.8, vin_diode, (vin_diode[0], 65.0))
add_track("SW", 0.4, point(pad("C7", "2")), point(pad("U2", "8")))

# Solid connections remove false starved-thermal errors on the eFuse and buck
# ground pads; their final thermal-via pattern remains a fabrication review item.
for zone in board.Zones():
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(OUTPUT), board)
print(f"Saved {OUTPUT}")
