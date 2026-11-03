#!/usr/bin/env python3
"""Make Cloudflare DNS match dns/records.json.

Usage: CLOUDFLARE_API_TOKEN=... python3 dns/sync.py [--apply]
Without --apply it only prints the plan. All records are DNS-only (not proxied):
GitHub Pages issues its own certificate, and the Sharif server is unreachable
from Cloudflare's edge.
"""
import json, os, sys, urllib.request, urllib.error

API = "https://api.cloudflare.com/client/v4"
MANAGED_TYPES = {"A", "AAAA", "CNAME"}
TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN")
if not TOKEN:
    if os.environ.get("GITHUB_ACTIONS"):
        print("::warning::Repository secret CLOUDFLARE_API_TOKEN is not set; DNS was not changed.")
        sys.exit(0)
    sys.exit("CLOUDFLARE_API_TOKEN is not set")
APPLY = "--apply" in sys.argv

def cf(method, path, body=None):
    req = urllib.request.Request(API + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        data = json.load(e)
    if not data.get("success"):
        sys.exit(f"Cloudflare API error on {method} {path}: {data.get('errors')}")
    return data

cfg = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "records.json")))
zones = cf("GET", f"/zones?name={cfg['zone']}")["result"]
if not zones:
    sys.exit(f"zone {cfg['zone']} not visible to this token")
zid = zones[0]["id"]

existing, page = [], 1
while True:
    d = cf("GET", f"/zones/{zid}/dns_records?per_page=100&page={page}")
    existing += d["result"]
    if page >= d["result_info"]["total_pages"]:
        break
    page += 1

deletes, creates, updates = [], [], []
for name, wanted in cfg["records"].items():
    have = [r for r in existing if r["name"] == name and r["type"] in MANAGED_TYPES]
    want = {(w["type"], w["content"]) for w in wanted}
    for r in have:
        if (r["type"], r["content"]) not in want:
            deletes.append(r)
        elif r.get("proxied") or r.get("ttl") != 1:
            updates.append(r)
    have_keys = {(r["type"], r["content"]) for r in have}
    creates += [{"type": t, "name": name, "content": c} for t, c in sorted(want - have_keys)]

for r in deletes: print(f"- delete {r['type']:5} {r['name']:28} {r['content']}")
for r in updates: print(f"~ update {r['type']:5} {r['name']:28} {r['content']} -> DNS only, TTL auto")
for r in creates: print(f"+ create {r['type']:5} {r['name']:28} {r['content']}")
if not (deletes or creates or updates):
    print("Cloudflare already matches dns/records.json")
    sys.exit(0)
if not APPLY:
    print("\nPlan only. Run with --apply to make these changes.")
    sys.exit(0)

for r in deletes:   # first, so a CNAME can replace an A record of the same name
    cf("DELETE", f"/zones/{zid}/dns_records/{r['id']}")
for r in updates:
    cf("PATCH", f"/zones/{zid}/dns_records/{r['id']}", {"proxied": False, "ttl": 1})
for r in creates:
    cf("POST", f"/zones/{zid}/dns_records", {**r, "proxied": False, "ttl": 1})
print(f"\nApplied: {len(deletes)} deleted, {len(updates)} updated, {len(creates)} created.")
