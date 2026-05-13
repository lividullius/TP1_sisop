"""
Renders simulation tick records as a self-contained HTML Gantt chart.
No external dependencies — pure Python string generation.
"""
from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .simulation_engine import TickRecord
    from .pcb import PCB

#asfas
# ── colour palette ────────────────────────────────────────────────────────────
_STATE_COLORS = {
    "EXECUTANDO": "#22c55e",   # green
    "BLOQUEADO":  "#f97316",   # orange
    "PRONTO":     "#60a5fa",   # blue
    "FINALIZADO": "#d1d5db",   # light gray
    "TERMINADO":  "#9ca3af",   # mid gray
}
_IDLE_COLOR      = "#f9fafb"
_PREEMPT_COLOR   = "#7c3aed"   # purple badge
_MISS_BORDER     = "#ef4444"   # red border for deadline miss
_DEADLINE_COLOR  = "#dc2626"   # vertical deadline marker


def _event_tags(events: List[str]) -> dict:
    """Parse prefixed event strings into a structured dict for a single tick."""
    result = {"preemption": False, "io_block": False, "deadline_miss": [],
              "arrival": [], "unblock": [], "halt": False}
    for e in events:
        if e.startswith("preemption:"):
            result["preemption"] = True
        elif e.startswith("io_block:"):
            name = e.split(":")[1].split(" ")[0]
            result["io_block"] = True
        elif e.startswith("deadline_miss:"):
            result["deadline_miss"].append(e.split(":")[1])
        elif e.startswith("arrival:"):
            result["arrival"].append(e.split(":")[1].split(" ")[0])
        elif e.startswith("unblock:"):
            result["unblock"].append(e.split(":")[1])
        elif e.startswith("halt:"):
            result["halt"] = True
    return result


def _cell(state: str, record, proc_name: str, deadlines_at_tick: bool) -> str:
    """Return a <td> element for one process at one tick."""
    tags = _event_tags(record.events)
    bg   = _STATE_COLORS.get(state, _IDLE_COLOR)

    # extra border for deadline miss
    border = f"border: 2px solid {_MISS_BORDER};" if proc_name in tags["deadline_miss"] else ""

    # tooltip
    tip_parts = [f"t={record.t}", f"{proc_name}: {state}"]
    if record.running == proc_name and record.instruction:
        tip_parts.append(f"instr: {record.instruction}")
    for e in record.events:
        tip_parts.append(e)
    tooltip = " | ".join(tip_parts)

    # badges inside cell
    badges = ""
    if tags["preemption"] and record.running == proc_name:
        badges += f'<span class="badge preempt" title="EDF preemption">▶</span>'
    if tags["io_block"] and state == "BLOQUEADO":
        badges += f'<span class="badge io" title="I/O block">⏸</span>'
    if proc_name in tags["deadline_miss"]:
        badges += f'<span class="badge miss" title="Deadline miss">!</span>'
    if deadlines_at_tick:
        badges += f'<span class="badge dl" title="Deadline">◆</span>'

    return (
        f'<td style="background:{bg};{border}" title="{tooltip}">'
        f'{badges}</td>'
    )


def render_html(
    tick_records: "List[TickRecord]",
    all_pcbs: "List[PCB]",
    filepath: str,
) -> None:
    """Build and write a self-contained HTML Gantt chart."""

    if not tick_records:
        return

    max_t   = tick_records[-1].t + 1
    names   = [p.name for p in all_pcbs]

    # collect all absolute deadlines per process across all periods
    # we reconstruct them from tick_records events
    deadlines: dict[str, set] = {n: set() for n in names}
    for rec in tick_records:
        for e in rec.events:
            if e.startswith("arrival:") or e.startswith("reactivation:"):
                # format: "arrival:T1 (deadline=12)"
                try:
                    dl = int(e.split("deadline=")[1].rstrip(")"))
                    pname = e.split(":")[1].split(" ")[0]
                    if pname in deadlines:
                        deadlines[pname].add(dl)
                except (IndexError, ValueError):
                    pass

    # ── HTML head ─────────────────────────────────────────────────────────────
    html = ["""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Gantt EDF — TP1 Sistemas Operacionais</title>
<style>
  body { font-family: 'Segoe UI', sans-serif; background: #f1f5f9; padding: 24px; color: #1e293b; }
  h1   { font-size: 1.4rem; margin-bottom: 4px; }
  p.sub { font-size: .85rem; color: #64748b; margin-bottom: 24px; }

  .container { overflow-x: auto; }

  table.gantt {
    border-collapse: collapse;
    table-layout: fixed;
    font-size: 12px;
  }
  table.gantt th, table.gantt td {
    width: 28px;
    min-width: 28px;
    height: 32px;
    text-align: center;
    vertical-align: middle;
    border: 1px solid #e2e8f0;
    padding: 0;
    position: relative;
  }
  table.gantt th.label-col, table.gantt td.label-col {
    width: 72px;
    min-width: 72px;
    text-align: right;
    padding-right: 8px;
    background: #f8fafc;
    font-weight: 600;
    border: none;
    position: sticky;
    left: 0;
    z-index: 2;
  }
  table.gantt thead th {
    background: #f8fafc;
    font-weight: 600;
    color: #475569;
    border-bottom: 2px solid #cbd5e1;
    position: sticky;
    top: 0;
    z-index: 1;
  }
  table.gantt thead th.label-col { z-index: 3; }

  .badge {
    display: inline-block;
    font-size: 9px;
    line-height: 1;
    border-radius: 3px;
    padding: 1px 2px;
    margin: 1px;
    font-weight: 700;
    cursor: default;
  }
  .badge.preempt { background: #7c3aed; color: #fff; }
  .badge.io      { background: #ea580c; color: #fff; }
  .badge.miss    { background: #dc2626; color: #fff; }
  .badge.dl      { background: #dc2626; color: #fff; font-size: 8px; }

  /* legend */
  .legend { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 20px; font-size: 13px; }
  .legend-item { display: flex; align-items: center; gap: 6px; }
  .legend-swatch { width: 18px; height: 18px; border-radius: 3px; border: 1px solid #cbd5e1; }

  /* summary table */
  table.summary { border-collapse: collapse; margin-top: 28px; font-size: 13px; }
  table.summary th, table.summary td { padding: 6px 14px; border: 1px solid #e2e8f0; }
  table.summary th { background: #f1f5f9; font-weight: 600; }
  table.summary tr:nth-child(even) td { background: #f8fafc; }

  /* events log */
  .events { margin-top: 28px; }
  .events h2 { font-size: 1rem; margin-bottom: 8px; }
  .events ul { list-style: none; padding: 0; font-size: 12px; font-family: monospace;
               max-height: 260px; overflow-y: auto;
               background: #fff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px; }
  .events li { padding: 2px 0; border-bottom: 1px solid #f1f5f9; }
  .ev-preempt  { color: #7c3aed; }
  .ev-block    { color: #ea580c; }
  .ev-miss     { color: #dc2626; font-weight: 700; }
  .ev-arrival  { color: #0284c7; }
  .ev-unblock  { color: #16a34a; }
  .ev-halt     { color: #6b7280; }
  .ev-period   { color: #0f766e; }
</style>
</head>
<body>
<h1>Gantt Chart — Escalonamento EDF</h1>
<p class="sub">TP1 Sistemas Operacionais · PUCRS · Passe o mouse sobre as células para detalhes.</p>
<div class="container">
"""]

    # ── Gantt table ───────────────────────────────────────────────────────────
    html.append('<table class="gantt">')

    # header row: tick numbers
    html.append("<thead><tr>")
    html.append('<th class="label-col">Processo</th>')
    for rec in tick_records:
        html.append(f"<th>{rec.t}</th>")
    html.append("</tr></thead>")

    # one row per process
    html.append("<tbody>")
    for p in all_pcbs:
        html.append(f'<tr><td class="label-col">{p.name}</td>')
        for rec in tick_records:
            state = rec.states.get(p.name, "TERMINADO")
            dl_marker = rec.t in deadlines[p.name]
            html.append(_cell(state, rec, p.name, dl_marker))
        html.append("</tr>")

    # CPU row (idle / running)
    html.append('<tr><td class="label-col" style="color:#94a3b8;">CPU</td>')
    for rec in tick_records:
        if rec.running:
            bg  = _STATE_COLORS["EXECUTANDO"]
            tip = f"t={rec.t} | {rec.running} executa: {rec.instruction or '?'}"
            cell = f'<td style="background:{bg}" title="{tip}">{rec.running}</td>'
        else:
            tip  = f"t={rec.t} | CPU ociosa"
            cell = f'<td style="background:{_IDLE_COLOR};color:#94a3b8" title="{tip}">—</td>'
        html.append(cell)
    html.append("</tr>")

    html.append("</tbody></table>")

    # ── Legend ────────────────────────────────────────────────────────────────
    legend_items = [
        (_STATE_COLORS["EXECUTANDO"], "Executando"),
        (_STATE_COLORS["PRONTO"],     "Pronto"),
        (_STATE_COLORS["BLOQUEADO"],  "Bloqueado (I/O)"),
        (_STATE_COLORS["FINALIZADO"], "Período concluído"),
        (_STATE_COLORS["TERMINADO"],  "Terminado (SYSCALL 0)"),
        (_IDLE_COLOR,                 "CPU ociosa"),
    ]
    html.append('<div class="legend">')
    for color, label in legend_items:
        html.append(
            f'<div class="legend-item">'
            f'<div class="legend-swatch" style="background:{color}"></div>'
            f'<span>{label}</span></div>'
        )
    html.append("</div>")

    # badge legend
    html.append('<div class="legend" style="margin-top:10px">')
    badge_items = [
        ("preempt", "▶", "Preempção EDF"),
        ("io",      "⏸", "Início de bloqueio I/O"),
        ("miss",    "!",  "Deadline miss"),
        ("dl",      "◆",  "Deadline absoluto"),
    ]
    for cls, sym, label in badge_items:
        html.append(
            f'<div class="legend-item">'
            f'<span class="badge {cls}">{sym}</span>'
            f'<span>{label}</span></div>'
        )
    html.append("</div>")

    # ── Summary table ─────────────────────────────────────────────────────────
    html.append('<table class="summary"><thead><tr>')
    for col in ("Processo", "Arrival", "Período (Pi)", "Comp. Time (Ci)",
                "Períodos completos", "Deadline misses"):
        html.append(f"<th>{col}</th>")
    html.append("</tr></thead><tbody>")
    for p in all_pcbs:
        miss_style = ' style="color:#dc2626;font-weight:700"' if p.deadline_misses else ""
        html.append(
            f"<tr>"
            f"<td>{p.name}</td>"
            f"<td>{p.arrival_time}</td>"
            f"<td>{p.period}</td>"
            f"<td>{p.computation_time}</td>"
            f"<td>{p.periods_completed}</td>"
            f"<td{miss_style}>{p.deadline_misses}</td>"
            f"</tr>"
        )
    html.append("</tbody></table>")

    # ── Events log ────────────────────────────────────────────────────────────
    html.append('<div class="events"><h2>Log de eventos</h2><ul>')
    for rec in tick_records:
        for e in rec.events:
            if e.startswith("preemption:"):
                css = "ev-preempt"
            elif e.startswith("io_block:"):
                css = "ev-block"
            elif e.startswith("deadline_miss:"):
                css = "ev-miss"
            elif e.startswith("arrival:") or e.startswith("reactivation:"):
                css = "ev-arrival"
            elif e.startswith("unblock:"):
                css = "ev-unblock"
            elif e.startswith("halt:"):
                css = "ev-halt"
            elif e.startswith("period_end:"):
                css = "ev-period"
            else:
                css = ""
            html.append(f'<li class="{css}">t={rec.t:3d} &nbsp; {e}</li>')
    html.append("</ul></div>")

    html.append("</div></body></html>")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(html))
