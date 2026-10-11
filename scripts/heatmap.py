from datetime import date


COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
CELL, GAP = 11, 3
LEFT, TOP = 32, 22


def level(n, q):
    if n == 0:
        return 0
    for i, edge in enumerate(q, 1):
        if n <= edge:
            return i
    return 4


def render(weeks, total):
    counts = sorted(d["contributionCount"] for w in weeks for d in w["contributionDays"] if d["contributionCount"])
    q = [counts[int(len(counts) * f)] for f in (0.25, 0.5, 0.75)] if counts else [1, 2, 3]
    width = LEFT + len(weeks) * (CELL + GAP) + 10
    height = TOP + 7 * (CELL + GAP) + 34
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{total} contributions in the last year">',
           '<style>text{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;font-size:10px;fill:#8b949e}</style>',
           f'<rect width="{width}" height="{height}" rx="6" fill="#0d1117"/>']
    last_month = None
    for wi, week in enumerate(weeks):
        x = LEFT + wi * (CELL + GAP)
        first = date.fromisoformat(week["contributionDays"][0]["date"])
        if first.month != last_month and wi < len(weeks) - 2:
            if last_month is not None or first.day <= 7:
                out.append(f'<text x="{x}" y="{TOP - 7}">{first.strftime("%b")}</text>')
            last_month = first.month
        for d in week["contributionDays"]:
            wd = (date.fromisoformat(d["date"]).weekday() + 1) % 7
            y = TOP + wd * (CELL + GAP)
            n = d["contributionCount"]
            out.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{COLORS[level(n, q)]}" stroke="#1b1f230f">'
                       f'<title>{n} contribution{"s" if n != 1 else ""} on {d["date"]}</title></rect>')
    for wd, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(f'<text x="4" y="{TOP + wd * (CELL + GAP) + 9}">{label}</text>')
    base = TOP + 7 * (CELL + GAP) + 16
    out.append(f'<text x="{LEFT}" y="{base}">{total:,} contributions in the last year</text>')
    lx = width - 10 - 5 * (CELL + GAP) - 34
    out.append(f'<text x="{lx - 30}" y="{base}">Less</text>')
    for i, c in enumerate(COLORS):
        out.append(f'<rect x="{lx + i * (CELL + GAP)}" y="{base - 9}" width="{CELL}" height="{CELL}" rx="2" fill="{c}"/>')
    out.append(f'<text x="{lx + 5 * (CELL + GAP) + 4}" y="{base}">More</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"
