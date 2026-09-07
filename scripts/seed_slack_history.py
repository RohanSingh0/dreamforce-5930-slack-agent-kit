#!/usr/bin/env python3
"""Give your agent something to find when it searches Slack.

Without this, the agent's Slack search returns nothing and the resolution card has no
"From Slack" evidence - you get the Salesforce half of the demo only. This posts a small
amount of history into your two channels so the search has real material.

It is deliberately additive: it never deletes anything, and it refuses to run twice in
the same channel rather than duplicating itself.

    python3 scripts/seed_slack_history.py

Needs `SLACK_USER_TOKEN` in `.env` (the `xoxp-` one) and both channels to exist with the
app invited. Canvases need the `canvases:write` user scope, which the manifest requests.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import time
import urllib.parse
import urllib.request

SUPPORT_CHANNEL = "grillmaster-support"
REPS_CHANNEL = "grillmaster-reps"

# Stamped invisibly on every seeded parent so a second run can detect itself.
MARKER = "\u200b"

SUPPORT_THREADS = [
    {
        "parent": (
            "Igniter on my GM-450 won't spark at all. Tried new batteries, nothing. "
            "Bought it last month."
        ),
        "reply": "Thanks for reporting it — we've raised this with the team and someone will follow up.",
    },
    {
        "parent": (
            "My GM-450 lights fine but the left burner runs noticeably cooler than the "
            "right one. Is that normal?"
        ),
        "reply": "Not normal, no. We're looking into it and will come back to you shortly.",
    },
    {
        "parent": "Is the grease tray on the GM-320 dishwasher safe?",
        "reply": "It is — top rack, and let it dry fully before refitting.",
    },
]

# The first two are what the agent actually cites. The third is deliberate noise, so the
# search has to be selective rather than returning everything in the channel.
REPS_THREADS = [
    {
        "parent": (
            "Third GM-450 igniter failure this month and every serial starts GM450-B7. "
            "This looks like a batch problem rather than three unlucky units — worth "
            "getting quality engineering to look at the whole run."
        ),
        "reply": (
            "Quality engineering came back: confirmed supplier defect in the igniter "
            "module across the entire batch B7 manufacturing run. They've pre-authorised "
            "free replacement parts for any batch B7 unit still inside warranty, and we "
            "should not be asking customers for proof of defect. Written up as KB-2210."
        ),
    },
    {
        "parent": (
            "Heads up on batch B7 diagnosis: the ground fault in the igniter module also "
            "disrupts gas flow to the adjacent burner, which is why customers report "
            "uneven heating alongside the no-spark fault."
        ),
        "reply": (
            "Right — so when uneven heating is reported, replace the burner tube "
            "GM450-BRN-04 as well as the igniter assembly GM450-IGN-R2. Replacing only "
            "the igniter leaves the heating complaint unresolved and we get a second "
            "contact."
        ),
    },
    {
        "parent": (
            "GM-320 grease tray rail complaints are ticking up — six this month against "
            "one or two normally. Anyone know if the supplier changed?"
        ),
        "reply": (
            "Tooling change at the supplier in July, tolerances drifted. Not a safety "
            "issue and not batch-restricted, so we're handling these case by case rather "
            "than pre-authorising."
        ),
    },
]

REPS_CANVAS_TITLE = "Warranty & Replacement Policy (Internal)"
REPS_CANVAS = """\
# Warranty & Replacement Policy (Internal)

## Pre-authorised replacements

| Product | Batch | Fault | Action |
|---|---|---|---|
| GM-450 | B7 | Igniter module ground fault | Free replacement of GM450-IGN-R2 and GM450-BRN-04 while in warranty. No proof of defect required. |

Replace both parts when uneven heating is reported. The ground fault disrupts gas flow to
the adjacent burner, so an igniter-only replacement leaves the heat complaint unresolved.

## Not pre-authorised

| Product | Fault | Action |
|---|---|---|
| GM-320 | Grease tray rail tolerance | Case by case. Supplier tooling drift, not a safety issue. |
| GM-600 | Lid hinge | Recall closed. Do not use the old runbook. |

Standard warranty is 24 months from purchase.
"""


def load_env() -> None:
    env = pathlib.Path(".env")
    if not env.exists():
        sys.exit("No .env found. Run this from the project root.")
    for line in env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def call(method: str, token: str, **params) -> dict:
    """Slack Web API. team_id is required on org-scoped tokens, harmless otherwise."""
    if TEAM_ID:
        params.setdefault("team_id", TEAM_ID)
    url = f"https://slack.com/api/{method}?" + urllib.parse.urlencode(
        {k: v for k, v in params.items() if v is not None}
    )
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def find_channel(token: str, name: str) -> str | None:
    cursor = None
    while True:
        resp = call(
            "conversations.list",
            token,
            types="public_channel,private_channel",
            limit=200,
            cursor=cursor,
        )
        if not resp.get("ok"):
            sys.exit(f"conversations.list failed: {resp.get('error')}")
        for channel in resp.get("channels", []):
            if channel.get("name") == name:
                return channel["id"]
        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            return None


def already_seeded(token: str, channel: str) -> bool:
    resp = call("conversations.history", token, channel=channel, limit=100)
    return any(MARKER in (m.get("text") or "") for m in resp.get("messages", []))


def seed(token: str, channel: str, threads: list[dict], label: str) -> None:
    if already_seeded(token, channel):
        print(f"  {label}: already seeded, skipping")
        return
    for thread in threads:
        parent = call(
            "chat.postMessage", token, channel=channel, text=thread["parent"] + MARKER
        )
        if not parent.get("ok"):
            print(f"  {label}: post failed ({parent.get('error')})")
            return
        call(
            "chat.postMessage",
            token,
            channel=channel,
            thread_ts=parent["ts"],
            text=thread["reply"],
        )
        time.sleep(1)  # stay well inside rate limits
    print(f"  {label}: {len(threads)} threads posted")


def add_canvas(token: str, channel: str, title: str, markdown: str) -> None:
    resp = call(
        "conversations.canvases.create",
        token,
        channel_id=channel,
        document_content=json.dumps({"type": "markdown", "markdown": markdown}),
        title=title,
    )
    if resp.get("ok"):
        print("  canvas created")
    else:
        print(
            f"  canvas skipped ({resp.get('error')}) — not fatal, the threads matter more"
        )


if __name__ == "__main__":
    load_env()
    TOKEN = os.environ.get("SLACK_USER_TOKEN", "").strip()
    if not TOKEN.startswith("xoxp-"):
        sys.exit("SLACK_USER_TOKEN must be set in .env and start with xoxp-")

    TEAM_ID = None
    auth = call("auth.test", TOKEN)
    if not auth.get("ok"):
        sys.exit(f"auth.test failed: {auth.get('error')}")
    print(f"Authenticated as {auth.get('user')} on {auth.get('team')}")

    # Most Web API methods need team_id, and on Enterprise Grid the id auth.test
    # returns is the *enterprise* - passing it gets you `team_access_not_granted`.
    # The workspace ids live behind auth.teams.list.
    if auth.get("is_enterprise_install"):
        teams = call("auth.teams.list", TOKEN)
        if not teams.get("ok") or not teams.get("teams"):
            sys.exit(
                "This is an Enterprise Grid org and auth.teams.list returned nothing. "
                "Set TEAM_ID by hand to your workspace id (starts with T)."
            )
        workspaces = teams["teams"]
        TEAM_ID = workspaces[0]["id"]
        if len(workspaces) > 1:
            print(
                "  workspaces found:",
                ", ".join(f"{w['name']} ({w['id']})" for w in workspaces),
            )
            print(f"  using the first: {workspaces[0]['name']}")
        else:
            print(f"  Grid org, using workspace {workspaces[0]['name']} ({TEAM_ID})")
    else:
        TEAM_ID = auth.get("team_id")

    support = find_channel(TOKEN, SUPPORT_CHANNEL)
    reps = find_channel(TOKEN, REPS_CHANNEL)
    if not support:
        sys.exit(f"Could not find #{SUPPORT_CHANNEL}. Create it and invite the app.")
    if not reps:
        sys.exit(f"Could not find #{REPS_CHANNEL}. Create it and invite the app.")

    seed(TOKEN, support, SUPPORT_THREADS, f"#{SUPPORT_CHANNEL}")
    seed(TOKEN, reps, REPS_THREADS, f"#{REPS_CHANNEL}")
    add_canvas(TOKEN, reps, REPS_CANVAS_TITLE, REPS_CANVAS)

    print("\nDone. Restart `slack run` is not needed — this only changed Slack.")
