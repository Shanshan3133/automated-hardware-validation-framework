from __future__ import annotations

import csv
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from .models import Status, TestResult


def _chart(result: TestResult) -> str:
    points = result.measurements
    if len(points) < 2:
        return ""
    stride = max(1, len(points) // 240)
    points = points[::stride]
    xs = [p.stimulus for p in points]
    ys = [p.value for p in points]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    if xmax == xmin:
        xmax = xmin + 1
    if ymax == ymin:
        ymax = ymin + 1
    pad, width, height = 34, 820, 190
    coords = []
    for x, y in zip(xs, ys):
        px = pad + (x - xmin) / (xmax - xmin) * (width - 2 * pad)
        py = height - pad - (y - ymin) / (ymax - ymin) * (height - 2 * pad)
        coords.append(f"{px:.1f},{py:.1f}")
    xunit = html.escape(points[0].stimulus_unit)
    yunit = html.escape(points[0].unit)
    trip_dots = "".join(
        f"<circle cx='{pad + (p.stimulus-xmin)/(xmax-xmin)*(width-2*pad):.1f}' "
        f"cy='{height-pad-(p.value-ymin)/(ymax-ymin)*(height-2*pad):.1f}' r='4'/>"
        for p in points if p.note == "TRIP")
    return f"""<svg class='chart' viewBox='0 0 {width} {height}' role='img' aria-label='{html.escape(result.name)} measurements'>
<line x1='{pad}' y1='{height-pad}' x2='{width-pad}' y2='{height-pad}'/><line x1='{pad}' y1='{pad}' x2='{pad}' y2='{height-pad}'/>
<polyline points='{' '.join(coords)}'/><g class='trip'>{trip_dots}</g>
<text x='{pad}' y='{height-8}'>{xmin:.3g} {xunit}</text><text x='{width-pad}' y='{height-8}' text-anchor='end'>{xmax:.3g} {xunit}</text>
<text x='4' y='{pad}'>{ymax:.4g} {yunit}</text><text x='4' y='{height-pad}'>{ymin:.4g} {yunit}</text></svg>"""


def write_results(output: Path, results: list[TestResult], metadata: dict) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    for index, result in enumerate(results, 1):
        path = output / f"{index:02d}_{result.name.lower().replace(' ', '_')}.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["test", "stimulus", "stimulus_unit", "value", "unit", "note"])
            writer.writeheader()
            for row in result.measurements:
                writer.writerow(row.__dict__)
    payload = {"metadata": metadata, "results": [r.to_dict() for r in results]}
    (output / "results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report = output / "report.html"
    report.write_text(_html(results, metadata), encoding="utf-8")
    return report


def _html(results: list[TestResult], metadata: dict) -> str:
    passed = sum(r.status == Status.PASS for r in results)
    overall = "PASS" if passed == len(results) else "FAIL"
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = "".join(
        f"<tr><td>{html.escape(r.name)}</td><td><span class='{r.status.value.lower()}'>{r.status.value}</span></td>"
        f"<td>{html.escape(r.summary)}</td><td>{r.duration_s:.3f}s</td></tr>" for r in results)
    meta = "".join(f"<dt>{html.escape(str(k))}</dt><dd>{html.escape(str(v))}</dd>" for k, v in metadata.items())
    charts = "".join(
        f"<article class='plot'><div><h3>{html.escape(r.name)}</h3><span class='{r.status.value.lower()}'>{r.status.value}</span></div>"
        f"<p>{html.escape(r.summary)}</p>{_chart(r)}</article>" for r in results)
    return f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'>
<title>Hardware Validation Report</title><style>
:root{{--ink:#172033;--muted:#64748b;--pass:#087443;--fail:#b42318;--paper:#fff;--bg:#eef2f7}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,sans-serif}}
main{{max-width:1050px;margin:36px auto;padding:0 20px}}header,.card{{background:var(--paper);border-radius:14px;padding:26px;box-shadow:0 4px 18px #17203312;margin-bottom:18px}}
h1{{margin:0 0 6px;font-size:28px}}.sub{{color:var(--muted)}}.score{{display:flex;gap:20px;align-items:baseline;margin-top:20px}}.score strong{{font-size:42px}}.pass{{color:var(--pass);font-weight:750}}.fail,.error{{color:var(--fail);font-weight:750}}
table{{width:100%;border-collapse:collapse}}th,td{{padding:13px 10px;border-bottom:1px solid #e5eaf0;text-align:left}}th{{font-size:12px;text-transform:uppercase;color:var(--muted)}}
.plots{{display:grid;grid-template-columns:repeat(auto-fit,minmax(390px,1fr));gap:16px}}.plot{{border:1px solid #e5eaf0;border-radius:10px;padding:16px;min-width:0}}.plot>div{{display:flex;justify-content:space-between;align-items:center}}.plot h3{{margin:0}}.plot p{{color:var(--muted);margin:4px 0 10px}}.chart{{display:block;width:100%;height:auto;background:#f8fafc;border-radius:8px}}.chart line{{stroke:#94a3b8;stroke-width:1}}.chart polyline{{fill:none;stroke:#2563eb;stroke-width:2;vector-effect:non-scaling-stroke}}.chart text{{font-size:11px;fill:#64748b}}.chart .trip{{fill:#b42318}}
dl{{display:grid;grid-template-columns:max-content 1fr;gap:6px 18px}}dt{{font-weight:700}}dd{{margin:0;color:var(--muted)}}footer{{color:var(--muted);font-size:12px;text-align:center;padding:12px}}
@media(max-width:560px){{.plots{{grid-template-columns:1fr}}table{{font-size:12px}}th,td{{padding:8px 5px}}}}
</style></head><body><main><header><h1>Hardware Validation Report</h1><div class='sub'>{html.escape(str(metadata.get('dut', 'DUT')))}</div>
<div class='score'><strong class='{overall.lower()}'>{overall}</strong><span>{passed}/{len(results)} tests passed</span></div></header>
<section class='card'><table><thead><tr><th>Test</th><th>Status</th><th>Result</th><th>Time</th></tr></thead><tbody>{rows}</tbody></table></section>
<section class='card'><h2>Measurement plots</h2><div class='plots'>{charts}</div></section>
<section class='card'><h2>Run metadata</h2><dl>{meta}<dt>generated_utc</dt><dd>{generated}</dd></dl></section>
<footer>Raw measurements and machine-readable results are stored beside this report.</footer></main></body></html>"""
