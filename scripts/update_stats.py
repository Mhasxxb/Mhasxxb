import json
import os
import re
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone

USER = os.environ.get("GH_USER", "Mhasxxb")
TOKEN = os.environ["GH_TOKEN"]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from heatmap import heatmap_width, render, render_streak

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
README = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "README.md")


def gql(query, **variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        body = json.load(r)
    if "errors" in body:
        raise SystemExit(body["errors"])
    return body["data"]


base = gql("""
query($login: String!) {
  user(login: $login) {
    createdAt
    pullRequests { totalCount }
    merged: pullRequests(states: MERGED) { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false) { totalCount }
  }
}""", login=USER)["user"]

os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
saved_path = os.path.join(ROOT, "assets", "calendar.json")
saved = {}
if os.path.exists(saved_path):
    with open(saved_path) as f:
        saved = json.load(f)

DAYS = "weeks { contributionDays { date contributionCount } }"
commits = 0
start_year = int(base["createdAt"][:4])
now = datetime.now(timezone.utc)
for year in range(start_year, now.year + 1):
    c = gql("""
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
          restrictedContributionsCount
          contributionCalendar { %s }
        }
      }
    }""" % DAYS, login=USER, **{"from": f"{year}-01-01T00:00:00Z",
                                "to": min(now, datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)).isoformat()})
    cc = c["user"]["contributionsCollection"]
    commits += cc["totalCommitContributions"] + cc["restrictedContributionsCount"]
    for week in cc["contributionCalendar"]["weeks"]:
        for d in week["contributionDays"]:
            saved[d["date"]] = max(d["contributionCount"], saved.get(d["date"], 0))

cal = gql("""
query($login: String!) {
  user(login: $login) { contributionsCollection { contributionCalendar { totalContributions %s } } }
}""" % DAYS, login=USER)["user"]["contributionsCollection"]["contributionCalendar"]
for week in cal["weeks"]:
    for d in week["contributionDays"]:
        saved[d["date"]] = max(d["contributionCount"], saved.get(d["date"], 0))
        d["contributionCount"] = saved[d["date"]]

with open(saved_path, "w") as f:
    json.dump(dict(sorted(saved.items())), f, indent=0)

contributions = sum(saved.values())
today = date.fromisoformat(max(d["date"] for w in cal["weeks"] for d in w["contributionDays"]))
year_total = max(cal["totalContributions"], sum(d["contributionCount"] for w in cal["weeks"] for d in w["contributionDays"]))
width = heatmap_width(len(cal["weeks"]))
with open(os.path.join(ROOT, "assets", "contributions.svg"), "w") as f:
    f.write(render(cal["weeks"], year_total))
with open(os.path.join(ROOT, "assets", "streak.svg"), "w") as f:
    f.write(render_streak(saved, contributions, date.fromisoformat(base["createdAt"][:10]), today, width))

with open(README) as f:
    previous = {m.group(1): int(m.group(2).replace(",", ""))
                for m in re.finditer(r"^([a-zA-Z ]+?) \.+ ([\d,]+)", f.read(), re.M)}
commits = max(commits, previous.get("commits", 0))
prs = max(base["pullRequests"]["totalCount"], previous.get("pull requests", 0))
merged = max(base["merged"]["totalCount"], previous.get("merged PRs", 0))
base["repositories"]["totalCount"] = max(base["repositories"]["totalCount"], previous.get("repositories", 0))
rate = round(merged / prs * 100) if prs else 0
rows = [
    ("total contributions", f"{contributions:,}"),
    ("commits", f"{commits:,}"),
    ("pull requests", f"{prs:,}"),
    ("merged PRs", f"{merged:,} ({rate}%)"),
    ("repositories", f"{base['repositories']['totalCount']:,}"),
]

pad = max(len(label) for label, _ in rows) + 4
block = "\n".join(f"{label} {'.' * (pad - len(label))} {value}" for label, value in rows)
with open(README) as f:
    readme = f.read()
readme = re.sub(r"(<!-- stats:start -->\n```bash\nhaseeb@github:~\$ gh stats --all-time\n)(?:.*?\n)?(```\n<!-- stats:end -->)",
                lambda m: m.group(1) + block + "\n" + m.group(2), readme, flags=re.S)
with open(README, "w") as f:
    f.write(readme)
print(block)
