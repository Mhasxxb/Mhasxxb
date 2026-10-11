import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

USER = os.environ.get("GH_USER", "Mhasxxb")
TOKEN = os.environ["GH_TOKEN"]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from heatmap import render

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

contributions = commits = 0
start_year = int(base["createdAt"][:4])
now = datetime.now(timezone.utc)
for year in range(start_year, now.year + 1):
    c = gql("""
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
          restrictedContributionsCount
          contributionCalendar { totalContributions }
        }
      }
    }""", login=USER, **{"from": f"{year}-01-01T00:00:00Z",
                         "to": min(now, datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)).isoformat()})
    cc = c["user"]["contributionsCollection"]
    contributions += cc["contributionCalendar"]["totalContributions"]
    commits += cc["totalCommitContributions"] + cc["restrictedContributionsCount"]

cal = gql("""
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
    }
  }
}""", login=USER)["user"]["contributionsCollection"]["contributionCalendar"]
os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
with open(os.path.join(ROOT, "assets", "contributions.svg"), "w") as f:
    f.write(render(cal["weeks"], cal["totalContributions"]))

prs, merged = base["pullRequests"]["totalCount"], base["merged"]["totalCount"]
rate = round(merged / prs * 100) if prs else 0
rows = [
    ("total contributions", f"{contributions:,}"),
    ("commits", f"{commits:,}"),
    ("pull requests", f"{prs:,}"),
    ("merged PRs", f"{merged:,} ({rate}%)"),
    ("repositories", f"{base['repositories']['totalCount']:,}"),
]

width = max(len(label) for label, _ in rows) + 4
block = "\n".join(f"{label} {'.' * (width - len(label))} {value}" for label, value in rows)
with open(README) as f:
    readme = f.read()
readme = re.sub(r"(<!-- stats:start -->\n```bash\nhaseeb@github:~\$ gh stats --all-time\n)(?:.*?\n)?(```\n<!-- stats:end -->)",
                lambda m: m.group(1) + block + "\n" + m.group(2), readme, flags=re.S)
with open(README, "w") as f:
    f.write(readme)
print(block)
