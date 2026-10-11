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


def _fmt(d, with_year):
    return d.strftime("%b %-d, %Y") if with_year else d.strftime("%b %-d")


def _span(a, b, today):
    if a is None:
        return ""
    with_year = a.year != today.year or b.year != today.year
    return _fmt(a, with_year) if a == b else f"{_fmt(a, with_year)} to {_fmt(b, with_year)}"


def streaks(days, today):
    ordered = sorted(days)
    longest, best = 0, (None, None)
    run, run_start = 0, None
    for iso in ordered:
        d = date.fromisoformat(iso)
        if d > today:
            break
        if days[iso]:
            run_start = d if run == 0 else run_start
            run += 1
            if run > longest:
                longest, best = run, (run_start, d)
        else:
            run = 0
    current, cur_start, cur_end = 0, None, None
    d = today if days.get(today.isoformat()) else date.fromordinal(today.toordinal() - 1)
    while days.get(d.isoformat()):
        current += 1
        cur_start, cur_end = d, cur_end or d
        d = date.fromordinal(d.toordinal() - 1)
    return current, (cur_start, cur_end), longest, best


def render_streak(days, total, first_day, today, width):
    current, cur_span, longest, best = streaks(days, today)
    h = 170
    col = width / 3
    total_dates = f"{_fmt(first_day, True)} to Present"
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}" viewBox="0 0 {width} {h}" role="img" aria-label="Contribution streaks">',
           '<style>text{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;text-anchor:middle}'
           '.num{font-size:28px;font-weight:700;fill:#e6edf3}.lbl{font-size:13px;fill:#8b949e}.dt{font-size:11px;fill:#6e7681}</style>',
           f'<rect width="{width}" height="{h}" rx="6" fill="#0d1117"/>',
           f'<line x1="{col:.0f}" y1="32" x2="{col:.0f}" y2="{h - 32}" stroke="#30363d"/>',
           f'<line x1="{2 * col:.0f}" y1="32" x2="{2 * col:.0f}" y2="{h - 32}" stroke="#30363d"/>']
    cx = col / 2
    out += [f'<text class="num" x="{cx:.0f}" y="78">{total:,}</text>',
            f'<text class="lbl" x="{cx:.0f}" y="108">Total Contributions</text>',
            f'<text class="dt" x="{cx:.0f}" y="130">{total_dates}</text>']
    cx = col * 1.5
    out += [f'<circle cx="{cx:.0f}" cy="70" r="38" fill="none" stroke="#39d353" stroke-width="5"/>',
            f'<text class="num" x="{cx:.0f}" y="80" style="fill:#39d353">{current}</text>',
            f'<text class="lbl" x="{cx:.0f}" y="132" style="fill:#39d353;font-weight:600">Current Streak</text>',
            f'<text class="dt" x="{cx:.0f}" y="150">{_span(*cur_span, today) if current else "Start one today"}</text>']
    cx = col * 2.5
    out += [f'<text class="num" x="{cx:.0f}" y="78">{longest}</text>',
            f'<text class="lbl" x="{cx:.0f}" y="108">Longest Streak</text>',
            f'<text class="dt" x="{cx:.0f}" y="130">{_span(*best, today)}</text>']
    out.append("</svg>")
    return "\n".join(out) + "\n"


def heatmap_width(n_weeks):
    return LEFT + n_weeks * (CELL + GAP) + 10
