# Build an Agent Using Slack Agent Kit

**Dreamforce 2026 · Session 5930 · Hands-on exercise guide**

You are going to build a Slack agent that handles a real customer problem end to end. It
searches Slack for context, delegates to an Agentforce agent in Salesforce for warranty
and defect research, combines both into one customer-ready reply, and posts it as a rich
card for a human to approve.

Roughly 40 minutes of building in the session, in five steps

---

## The scenario

A customer, **Jordan Reyes**, posts in your support channel:

> My new grill's igniter won't light and one of the burners isn't heating evenly.
> I bought it two weeks ago — can someone help me get this fixed or replaced?
> — Jordan Reyes

That signature matters, so don't drop it. The Salesforce lookup is by customer name. Without a name in the message the agent has nothing to look up, and you'll get *"No customer name was provided"* back from Salesforce instead of a warranty.

By the end you'll have an agent that answers: *this is a known manufacturing defect on
your batch, you're in warranty, here are the exact parts, and you qualify for a free
replacement* — with every fact traced to a Salesforce record, and a human approving
before the customer sees it.

---



## Before you start

Four things. Check them now, in this order.

**If you're missing the Anthropic key or Python 3.12, you have not wasted your time.**
Nobody expects everyone to arrive with both. Everything in this guide is a real build you
can finish afterwards: the code is public with a tagged commit per step, the Salesforce
credentials on your handout keep working, and the two gaps take about ten minutes to close
at home. Follow along, type it out, and run it this evening. The parts you'd miss today are
the reply appearing in Slack — not the understanding.

```bash
# 1. Python 3.12 or newer
python3 --version         # macOS ships 3.9 — you will need to upgrade

# 2. Slack CLI
slack version             # if missing:
# curl -fsSL https://downloads.slack-edge.com/slack-cli/install.sh | bash

# 3. An Anthropic API key  — needs a signup and a payment method,
echo $ANTHROPIC_API_KEY   #   so this is the one to do tonight if you don't have it.
                          #   console.anthropic.com → Settings → API Keys

# 4. A Slack workspace where you are an ADMIN
```

Without a key the agent cannot reason, so `slack run` will connect but never reply. That is
the expected result, not a broken build — carry on through the steps and it will work the
moment you add one.

> **If** `python3` **is older than 3.12**, install a newer one before continuing. The
> scaffold builds a virtual environment using whatever `python3` it finds, and an older
> one produces a broken install with a confusing pip error. If you have no admin rights:
>
> ```bash
> curl -fsSL https://astral.sh/uv/install.sh | sh
> uv python install 3.12
> ```



### Credentials for the shared Salesforce org

These point at a shared org that already contains the Agentforce agent, the customer
records and the Knowledge article.

You don't have anywhere to put them yet. In Step 1 you'll create a project, and copying
`.env.sample` to `.env` **in that project's root folder** gives you the file these go in.
Step 2 shows exactly what it should end up looking like. Nothing to do right now.

```bash
SF_MY_DOMAIN=https://<from-the-handout>.my.salesforce.com
SF_AGENT_ID=<from-the-handout>
SF_CONSUMER_KEY=<from-the-handout>
SF_CONSUMER_SECRET=<from-the-handout>
```

> **In the session?** You'll be handed these four values on the day. They point at a
> shared throwaway org that expires shortly after the workshop, so they are deliberately
> not in this repo.
>
> **Following along later?** You'll need your own org: an Agentforce agent with an Apex
> action that looks up the customer's asset, warranty and open cases, plus an External
> Client App using the client-credentials flow with the `sfap_api` scope. Everything from
> Step 3 onwards works against any agent that answers in plain text — only these four
> values change.

The Salesforce side — the Agentforce agent, its Apex action, the customer data, the
Knowledge article — is already built. You are building the Slack agent that calls it.

---

## Getting started — you have VS Code open, now what

Do these five things before Step 1. None of it is the build; it's getting to a terminal you
can build in.

### 1 · Open a terminal inside VS Code

**Terminal → New Terminal** from the menu, or **Ctrl+`** (Cmd+` on a Mac). A panel opens at
the bottom. Every command in this guide goes there.

### 2 · Choose where the project will live

The project doesn't exist yet — you're about to create it. Move to wherever you keep code:

```bash
cd ~/Documents          # or ~/code, or wherever you prefer
```

Whatever you pick, you'll end up with a new `grillmaster-agent` folder inside it.

### 3 · Check your three prerequisites

Run these three and compare the output. It takes twenty seconds and saves you from
discovering a problem four steps in:

```bash
python3 --version       # want 3.12 or higher
slack version           # want any version number
echo $ANTHROPIC_API_KEY # want something starting sk-ant-
```

| What you see | What it means |
|---|---|
| `Python 3.12.x` or higher | good |
| `Python 3.9.x` | too old — see the box above on `uv` |
| `command not found: slack` | install it: `curl -fsSL https://downloads.slack-edge.com/slack-cli/install.sh \| bash` |
| an empty line from `echo` | no key set — you can still do every step, you just won't get replies. See *Before you start*. |

### 4 · Clone the reference repo alongside — optional but worth it

You do **not** need this to build. You'll create your own project in Step 1. But having the
finished version sitting next to you is genuinely useful, for two reasons: if a paste goes
wrong you can compare against a known-good file, and if you fall behind you can jump
straight to the end of any step.

Put it in a *separate* folder from the project you're about to build, so the two don't get
confused:

```bash
cd ~/Documents
git clone https://github.com/RohanSingh0/dreamforce-5930-slack-agent-kit.git reference
```

That gives you `~/Documents/reference`. To see the finished state of any step:

```bash
cd ~/Documents/reference
git checkout step-3          # step-1 … step-5, or `main` for the finished agent
```

You can open that folder in a second VS Code window and keep it side by side with your own.

### 5 · Log in to Slack from the terminal

This is the fiddliest part of the whole setup, so here it is in detail:

```bash
slack login
```

It prints a line that looks like `/slackauthticket ABC123def456…` and then waits.

1. **Copy that whole line**, including the leading `/`.
2. Go to Slack, into **your own workspace** — not a corporate one — and open any channel or
   your own DMs.
3. Paste it into the message box and press Enter. Slack treats it as a command, not a
   message, so nothing gets posted publicly.
4. A confirmation dialog appears. Click **Confirm**.
5. Slack then shows you a **challenge code**. Copy it.
6. Paste it back into the terminal that's still waiting, and press Enter.

The terminal should confirm you're logged in and show your workspace name. If it says the
ticket expired, just run `slack login` again — they're short-lived.

> **Use a workspace where you are an admin.** `slack run` in Step 1 creates and installs an
> app, which needs admin rights. A corporate workspace will refuse.

Now you're ready.

---



## Step 1 — Scaffold and run · 5 min

You're logged in and sitting in the folder where the project should go. Create it:

```bash
slack create grillmaster-agent \
  -t slack-samples/bolt-python-support-agent \
  --subdir claude-agent-sdk

cd grillmaster-agent
code .                              # or: open the folder in your editor
```

### What you just made, and what you'll actually touch

You didn't start from an empty folder. `slack create` scaffolded a **working Slack agent**
from a template — 45 files, 32 of them Python — and it already runs. Everything you do from
here is modifying something that works, which is why every step ends with you seeing a
result in Slack rather than waiting until the end.

That's a lot of files to open a project onto. You will touch **eight** of the Python ones.
Ignore the rest; they are the framework doing its job.

| File | Step | |
|---|---|---|
| `pyproject.toml` | 1 | fix a stale package name |
| `.slack/hooks.json` | 1 | point it at the venv |
| `.env` | 1–2 | your keys and the Salesforce credentials |
| `agent/casey.py` | 2, 3, 4, 5 | the agent itself — prompt, tools, model |
| `agent/tools/agentforce.py` | 2 | **create** — calls Salesforce |
| `agent/tools/__init__.py` | 2, 4 | export each new tool |
| `agent/cards.py` | 4, 5 | **create** — the Block Kit card |
| `agent/tools/resolution_card.py` | 4, 5 | **create** — posting the card, as a tool |
| `listeners/customer_reply.py` | 5 | **create** — guards what the customer sees |
| `listeners/events/app_mentioned.py` | 5 | call that guard |
| `listeners/actions/resolution_buttons.py` | 5 | **create** — the Approve handler |
| `listeners/actions/__init__.py` | 5 | register the handler |

Two directories are worth knowing the difference between, because it's the shape of every
Bolt app. **`agent/`** is the reasoning — the prompt, the tools it can call, how it decides.
**`listeners/`** is Slack — what arrives, what gets posted, what happens when a button is
clicked. When you're unsure where something belongs, ask whether it's a decision or a Slack
event.



### Fix two things in the template

Both of these will bite you otherwise.

**1. A stale self-reference in** `pyproject.toml`**.** Find the `dev` extra and correct the
package name:

```toml
dev = [
    "grillmaster-agent[test]",   # was: bolt-python-support-agent-claude[test]
    "ruff==0.16.5",
]
```

**2. The hook runtime in** `.slack/hooks.json`**.** It calls bare `python3`, which resolves
to your system Python rather than the project venv, and fails with an opaque
`runtime_not_found`. Point it at the venv:

```json
{
  "hooks": {
    "get-hooks": ".venv/bin/python3 -m slack_cli_hooks.hooks.get_hooks"
  }
}
```



### Install and start

The scaffold already created a `.venv` using your **system** Python. If that isn't 3.12+,
its dependency install will have failed. Rebuild it either way — it takes seconds and
removes all doubt:

```bash
rm -rf .venv
python3.12 -m venv .venv          # or: uv venv --python 3.12
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.sample .env               # then add your ANTHROPIC_API_KEY

slack run
```

> `pip install` should end with a list of installed packages including `slack-bolt` and
> `claude-agent-sdk`. If it complains about `setup.py` or editable mode, your venv is on
> an old Python — check `python --version` inside the activated venv.

Choose your workspace, and grant access to the specific workspace rather than the whole
organisation.

> **If you get "Administrator approval is required"**, your workspace enforces app
> approval. An admin needs to approve it, or better, turn the requirement off:
> Integrations → Requests → Automation rules → **Default** → set resolution to
> *Approve*.

**Check it works:** create a channel, invite the app with `/invite @grillmaster-agent`,
and mention it. You should get a reply.

You have a live agent in Slack. It knows nothing about grills yet.

---



## Step 2 — Give it Salesforce · 9 min

This is the step that matters. One file turns a chatbot into something that reasons over
enterprise data.

Create `agent/tools/agentforce.py`:

```python
"""Delegate defect and warranty research to an Agentforce agent in Salesforce."""

import asyncio
import logging
import os
import time
import uuid

import aiohttp
from claude_agent_sdk import tool

logger = logging.getLogger(__name__)
AGENT_API = "https://api.salesforce.com/einstein/ai-agent/v1"
TIMEOUT = aiohttp.ClientTimeout(total=180)

_token: str | None = None
_expires_at = 0.0
_lock = asyncio.Lock()


async def _access_token(session: aiohttp.ClientSession) -> str:
    """Cache the token. Minting one per request triggers Maximum Logins Exceeded."""
    global _token, _expires_at
    async with _lock:
        if _token and time.time() < _expires_at - 120:
            return _token
        domain = os.environ["SF_MY_DOMAIN"].rstrip("/")
        async with session.post(
            f"{domain}/services/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": os.environ["SF_CONSUMER_KEY"],
                "client_secret": os.environ["SF_CONSUMER_SECRET"],
            },
        ) as resp:
            resp.raise_for_status()
            body = await resp.json()
        _token = body["access_token"]
        _expires_at = time.time() + int(body.get("expires_in", 1800))
        return _token


async def _ask(question: str) -> str:
    domain = os.environ["SF_MY_DOMAIN"].rstrip("/")
    agent_id = os.environ["SF_AGENT_ID"]

    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        headers = {
            "Authorization": f"Bearer {await _access_token(session)}",
            "Content-Type": "application/json",
        }

        # 1. open a session
        async with session.post(
            f"{AGENT_API}/agents/{agent_id}/sessions",
            headers=headers,
            json={
                "externalSessionKey": str(uuid.uuid4()),
                "instanceConfig": {"endpoint": domain},
                "streamingCapabilities": {"chunkTypes": ["Text"]},
                "bypassUser": False,
            },
        ) as resp:
            resp.raise_for_status()
            session_id = (await resp.json())["sessionId"]

        # 2. ask, then 3. always close
        try:
            async with session.post(
                f"{AGENT_API}/sessions/{session_id}/messages",
                headers=headers,
                json={"message": {"sequenceId": 1, "type": "Text", "text": question}},
            ) as resp:
                resp.raise_for_status()
                payload = await resp.json()
            return "\n\n".join(
                m.get("message", "") for m in payload.get("messages", []) if m.get("message")
            )
        finally:
            async with session.delete(
                f"{AGENT_API}/sessions/{session_id}",
                headers={**headers, "x-session-end-reason": "UserRequest"},
            ):
                pass


@tool(
    name="ask_agentforce_about_product_issue",
    description=(
        "Ask the GrillMaster Agentforce agent in Salesforce to research a customer's "
        "reported product problem. Returns whether a known manufacturing defect affects "
        "their unit, how many prior cases support that, the purchase date and warranty "
        "status, the Knowledge article documenting the fix and the replacement parts, "
        "and whether the customer qualifies for a free replacement under warranty. "
        "Call this for ANY report of a faulty grill. This is the only source of truth "
        "for warranty and defect information — never answer those from your own "
        "knowledge."
    ),
    input_schema={"customer_name": str, "reported_symptoms": str},
)
async def ask_agentforce_tool(args):
    question = (
        f'Customer {args["customer_name"]} reports: "{args["reported_symptoms"]}" '
        "Tell me whether a known defect applies, the warranty status, the relevant "
        "knowledge article, and whether they qualify for a free replacement part."
    )
    for attempt in (1, 2):
        try:
            started = time.time()
            answer = await _ask(question)
            logger.info("Agentforce answered in %.1fs", time.time() - started)
            return {"content": [{"type": "text", "text": answer}]}
        except Exception as exc:  # noqa: BLE001
            logger.warning("Agentforce attempt %d/2 failed: %s", attempt, exc)
            if attempt == 1:
                await asyncio.sleep(2)
    return {
        "content": [
            {
                "type": "text",
                "text": "The Salesforce lookup failed. Say so plainly and do not guess "
                "at warranty or defect details.",
            }
        ]
    }
```



### Add the credentials

Open `.env` — it's in the root of your project, the file you created in Step 1 with
`cp .env.sample .env`. It's a hidden file, so if your editor's file tree doesn't show it,
open it directly (`Cmd+P` in Cursor/Claude Code or VS Code, type `.env`) or edit it in the terminal
with `nano .env`.

When you're done it should look like this, with no quotes and no spaces around the `=`:

```bash
# came with the template — your own Anthropic key
ANTHROPIC_API_KEY=sk-ant-your-key-here

# the shared Salesforce org — copy these exactly
SF_MY_DOMAIN=https://<from-the-handout>.my.salesforce.com
SF_AGENT_ID=<from-the-handout>
SF_CONSUMER_KEY=<from-the-handout>
SF_CONSUMER_SECRET=<from-the-handout>

# your own Slack user token — needed for Slack search, see below
SLACK_USER_TOKEN=xoxp-...
```

`.env` is only read when the app starts, so **restart** `slack run` after editing it — a
hot reload won't pick up changes.

### Getting your Slack user token

Your agent searches Slack through Slack's hosted MCP server, and **that requires a *user*
token**. `slack run` only injects a bot token, so without this the search tools are never
registered — and the agent won't tell you. It will write something plausible onto the card
like *"Slack search unavailable this session"* rather than admitting it has no search tool.
That silent failure is worth seeing once; it's the same class of problem as an agent
answering without calling your tool.

In a **second terminal**, so you don't stop `slack run`:

```bash
slack app settings
```

That opens your app's configuration in the browser. Then:

1. Left nav → **Settings → Install App**
2. Copy the **User OAuth Token** — it starts `xoxp-`

Two things people get wrong here. The token lives under **Install App**, not under *OAuth &
Permissions* — that page shows your scopes but no tokens. And you want the `xoxp-` one, not
the **Bot** User OAuth Token starting `xoxb-`: `mcp.slack.com` rejects bot tokens outright,
which is the same reason `search.messages` does.

You don't need to reinstall. The template's manifest already requests the `search:read.*`
and `canvases:read` user scopes, so the token already exists — you're just reading it.

Paste it into `.env` as `SLACK_USER_TOKEN` and restart `slack run`. You'll see
`Slack MCP registered` in the log on the next mention, which is your confirmation.

### Register the tool

In `agent/tools/__init__.py`, export it:

```python
from .agentforce import ask_agentforce_tool     # add this import

__all__ = [
    "add_emoji_reaction_tool",
    "ask_agentforce_tool",                       # add this entry
    # ... leave the rest as they are
]
```

Then in `agent/casey.py`:

```python
from agent.tools import (
    add_emoji_reaction_tool,
    ask_agentforce_tool,                          # add
    mark_resolved_tool,
)

casey_tools_server = create_sdk_mcp_server(
    name="casey-tools",
    version="1.0.0",
    tools=[
        add_emoji_reaction_tool,
        ask_agentforce_tool,                          # add
        mark_resolved_tool,
    ],
)

CASEY_TOOLS = [
    "add_emoji_reaction",
    "ask_agentforce_about_product_issue",             # add
    "mark_resolved",
]
```

**Check it works:** restart `slack run`, then post Jordan's message in the channel:

```
@grillmaster-agent My new grill's igniter won't light and one of the burners
isn't heating evenly. I bought it two weeks ago — can someone help me get this
fixed or replaced? — Jordan Reyes
```

Type `@grill` and pick the app from autocomplete so Slack makes it a real mention; pasting
the text as plain characters won't trigger anything. Keep the `— Jordan Reyes` signature.
It should now come back with a real serial number, batch, warranty date and article
number — all read from Salesforce.

> **Notice what you did not write.** No SOQL, no Case queries, no warranty logic. The
> Agentforce agent already knew how to do that. You gave your agent a phone number for a
> specialist.

---



## Step 3 — Shape the behaviour · 6 min

Replace `CASEY_SYSTEM_PROMPT` in `agent/casey.py`:

```python
CASEY_SYSTEM_PROMPT = """\
You are the GrillMaster Co support agent, working inside Slack. When a customer reports
a problem with their grill, you research it and draft a customer-ready reply for a human
rep to approve.

You are the orchestrator. You know nothing about products, warranties or defects
yourself — you gather that from tools and synthesise it.

## WORKFLOW
1. React to the message with `add_emoji_reaction`.
2. Search Slack for prior threads on the same model or symptom, and for canvases
   covering warranty policy. Two or three searches, no more.
3. Call `ask_agentforce_about_product_issue` with the customer's name and their
   description of the problem.
4. Reply with one concise paragraph, then short labelled lines covering: the model and
   batch, whether a known defect applies and how many prior cases support it, the
   warranty status, the Knowledge article, and whether a free replacement is warranted.

## HARD RULES
Warranty status, defect status, dates, serial numbers, batch codes, article numbers and
part numbers come ONLY from `ask_agentforce_about_product_issue`. Never state any of
these from your own knowledge and never estimate them.

If the lookup fails or finds no record, say so plainly and do not speculate. A missing
answer is fine; an invented one is not.

Never invent a case number, part number or article number.
"""
```

**Check it works:** restart and mention the agent again. Same data, but now it reads like
a support professional rather than a chatbot.

> **The most under-appreciated part of agent building is tool descriptions.** The model
> chooses tools from their name and description alone. Vague description, and it skips
> your tool and answers from its own knowledge — which *looks* like it worked. Try
> shortening the description on `ask_agentforce_about_product_issue` to just "Ask
> Salesforce" and watch it stop calling it.

---



## Step 4 — Rich UI as a tool · 8 min

Create `agent/cards.py`:

```python
def build_resolution_card(
    *, customer_name, draft_message, product_summary="",
    warranty_status="", defect_status="", knowledge_article="", entitlement="",
) -> list[dict]:
    blocks = [
        {"type": "header",
         "text": {"type": "plain_text", "text": "Resolution ready for review"}},
        {"type": "context", "elements": [
            {"type": "mrkdwn",
             "text": f"*Customer:* {customer_name}  ·  {product_summary}"}]},
        {"type": "divider"},
        {"type": "section", "text": {"type": "mrkdwn", "text": draft_message}},
    ]

    fields = [
        {"type": "mrkdwn", "text": f"*{label}*\n{value}"}
        for label, value in (
            ("Warranty", warranty_status),
            ("Known defect", defect_status),
            ("Knowledge article", knowledge_article),
            ("Entitlement", entitlement),
        )
        if value
    ]
    if fields:
        blocks += [{"type": "divider"}, {"type": "section", "fields": fields}]

    blocks.append({
        "type": "actions",
        "block_id": "resolution_actions",
        "elements": [
            {"type": "button", "action_id": "resolution_approve", "style": "primary",
             "text": {"type": "plain_text", "text": "Approve & Send"}, "value": "ok"},
            {"type": "button", "action_id": "resolution_edit",
             "text": {"type": "plain_text", "text": "Edit"}, "value": "ok"},
        ],
    })
    return blocks
```

And `agent/tools/resolution_card.py`:

```python
from claude_agent_sdk import tool

from agent.cards import build_resolution_card
from agent.context import casey_deps_var


@tool(
    name="post_resolution_card",
    description=(
        "Post the final customer-ready update into the thread as a Block Kit card with "
        "Approve and Edit buttons. Call this ONCE as your last action, after you have "
        "called ask_agentforce_about_product_issue. Write draft_message as the text you "
        "would actually send the customer: plain English, no jargon, no internal IDs."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "customer_name": {"type": "string"},
            "draft_message": {"type": "string"},
            "product_summary": {"type": "string"},
            "warranty_status": {"type": "string"},
            "defect_status": {"type": "string"},
            "knowledge_article": {"type": "string"},
            "entitlement": {"type": "string"},
        },
        "required": ["customer_name", "draft_message"],
    },
)
async def post_resolution_card_tool(args):
    deps = casey_deps_var.get()
    await deps.client.chat_postMessage(
        channel=deps.channel_id,
        thread_ts=deps.thread_ts,
        blocks=build_resolution_card(**args),
        text=f"Resolution ready for review — {args['customer_name']}",
    )
    return {"content": [{"type": "text", "text": "Card posted. Do not repeat the draft."}]}
```

Register it the same way as Step 2, and add a closing instruction to the prompt:

```
5. Call `post_resolution_card` exactly once as your final action, then reply with one
   short sentence saying the draft is ready for review.
```

**Check it works:** restart and mention the agent. You get a formatted card with an
evidence grid and buttons.

> **Posting the card is a *tool the agent calls*, not something your listener does
> afterwards.** That keeps composing the interface inside the reasoning loop — the agent
> decides what goes on the card in the same pass that gathered the evidence.

---



## Step 5 — Human in the loop · 12 min

The card carries internal detail — batch codes, case counts, entitlement rules — that a
customer should not see. So it goes to a rep channel, and only the approved reply reaches
the customer.

Create a second channel, `#grillmaster-reps`, invite the app, and add its channel ID to
`.env`:

```bash
REP_CHANNEL=C0________
```

The buttons are now clicked in a *different channel* from where the reply must go, so each
one has to carry the customer's location.

Two edits to `agent/cards.py`. This is a **diff, not a whole file** — the `...` marks the
middle of the function, which you leave alone. Add `origin=""` to the signature, and
change both button `value` fields from `"ok"` to `origin`:

```python
def build_resolution_card(
    *, customer_name, draft_message, origin="", product_summary="",
    warranty_status="", defect_status="", knowledge_article="", entitlement="",
) -> list[dict]:
    ...
    blocks.append({
        "type": "actions",
        "block_id": "resolution_actions",
        "elements": [
            {"type": "button", "action_id": "resolution_approve", "style": "primary",
             "text": {"type": "plain_text", "text": "Approve & Send"},
             "value": origin},                                    # <- was "ok"
            {"type": "button", "action_id": "resolution_edit",
             "text": {"type": "plain_text", "text": "Edit"},
             "value": origin},                                    # <- was "ok"
        ],
    })
    return blocks
```

Then in `agent/tools/resolution_card.py`, replace the body of the tool function:

```python
import json
import os

async def post_resolution_card_tool(args):
    deps = casey_deps_var.get()
    rep_channel = os.environ.get("REP_CHANNEL", "").strip()

    blocks = build_resolution_card(
        origin=json.dumps({"c": deps.channel_id, "t": deps.thread_ts}),
        **args,
    )

    await deps.client.chat_postMessage(
        channel=rep_channel or deps.channel_id,
        # top-level in the rep channel; in-thread if there is no rep channel
        **({} if rep_channel else {"thread_ts": deps.thread_ts}),
        blocks=blocks,
        text=f"Resolution ready for review — {args['customer_name']}",
    )

    return {
        "content": [
            {
                "type": "text",
                "text": (
                    "Card posted to the rep channel — the customer cannot see it. "
                    "Your next and final message is posted verbatim into the "
                    "customer's thread; it is not a report back to an operator. "
                    "Write ONE neutral sentence saying their issue is with the team "
                    "and someone will follow up. Do not summarise what you did, do "
                    "not list the steps you took, and do not reveal warranty, defect "
                    "or part details."
                ),
            }
        ]
    }
```

Now create a **new file**, `listeners/actions/resolution_buttons.py`:

```python
async def handle_resolution_approve(ack, body, client, context, logger):
    await ack()
    origin = json.loads(body["actions"][0]["value"])
    blocks = body["message"]["blocks"]
    draft = next(b["text"]["text"] for b in blocks
                 if b.get("type") == "section" and "text" in b)

    # the customer-facing reply, into the customer's own thread
    await client.chat_postMessage(channel=origin["c"], thread_ts=origin["t"], text=draft)

    # stamp the card so the team can see it was handled
    kept = [b for b in blocks if b.get("block_id") != "resolution_actions"]
    kept.append({"type": "context", "elements": [
        {"type": "mrkdwn",
         "text": f":white_check_mark: Approved by <@{context.user_id}>"}]})
    await client.chat_update(channel=body["channel"]["id"], ts=body["message"]["ts"],
                            blocks=kept, text="Approved")
```

That file needs one import at the top:

```python
import json
```

(The other handlers in `listeners/actions/` import Bolt's types to annotate their
arguments. This one leaves them untyped to keep the step short, so it needs nothing else —
adding those imports here would just fail `ruff` as unused.)

Finally register it in `listeners/actions/__init__.py` — one import and one line inside
`register`:

```python
from .resolution_buttons import handle_resolution_approve      # add


def register(app: AsyncApp):
    app.action(re.compile(r"^category_"))(handle_issue_button)
    app.action("feedback")(handle_feedback_button)
    app.action("resolution_approve")(handle_resolution_approve)   # add
```

**Check it works:** post Jordan's message again, watch the card appear in the rep
channel, click Approve, and see the reply land in the customer's thread.

### Enforce it in code, because a prompt is not a guarantee

You have told the agent to reply to the customer with one neutral sentence. That is an
instruction, not a control. Ours ignored it: when the Agentforce lookup failed once, the
agent stopped following the instruction and started explaining itself instead — posting a
five-step internal report into the customer's thread that named the rep channel, the defect
batch and a canvas file id, and admitted a backend call had errored.

Nothing about the prompt was wrong. It simply stopped being obeyed under conditions we
hadn't rehearsed. So validate the one message the customer actually sees.

Create `listeners/customer_reply.py`:

```python
import re

SAFE_FALLBACK = (
    "Thanks for getting in touch — your issue has been picked up by our support "
    "team and someone will follow up with you shortly."
)

INTERNAL_TERMS = (
    "batch", "kb-", "agentforce", "salesforce", "knowledge article",
    "prior case", "entitlement", "warranty status", "grillmaster-reps",
)


def vet_customer_reply(text: str | None) -> tuple[str, str | None]:
    """Return (reply_to_send, reason_replaced). reason is None if the text was fine."""
    if not text or not text.strip():
        return SAFE_FALLBACK, "empty reply"

    candidate = text.strip()
    if len(candidate) > 420:
        return SAFE_FALLBACK, f"too long ({len(candidate)} chars)"
    for term in INTERNAL_TERMS:
        if term in candidate.lower():
            return SAFE_FALLBACK, f"contained internal term {term!r}"
    if candidate.count("\n") > 4 or re.search(r"^\s*[-*•]\s", candidate, re.MULTILINE):
        return SAFE_FALLBACK, "looked like a step-by-step report"

    return candidate, None
```

Then call it in `listeners/events/app_mentioned.py`, just before the reply is posted:

```python
from listeners.customer_reply import vet_customer_reply      # add


# ... where the agent's response_text is ready, before posting it:
if os.environ.get("REP_CHANNEL", "").strip():                # add this block
    original = response_text
    response_text, replaced = vet_customer_reply(response_text)
    if replaced:
        logger.warning(
            "Replaced the customer-facing reply (%s): %r", replaced, original[:200]
        )
```

Note it only fires when `REP_CHANNEL` is set — that's exactly when the thread is
customer-visible and the detail has gone elsewhere. Capture `original` *before* reassigning,
or your log will helpfully show you the replacement rather than the thing you wanted to see.

If the log stays quiet, the guard never had to fire and the agent behaved. That is the point:
it's insurance sitting behind correct behaviour, not a patch over a bad prompt.

### One more edit, or the review step is optional

You have just built a control: nothing reaches the customer until a human approves it. But
right now your agent can walk straight past it.

Look at how the template grants the Slack tools, in `agent/casey.py`:

```python
allowed_tools.append("mcp__slack-mcp__*")
```

That wildcard grants **all thirteen** Slack MCP tools, and five of them write —
`slack_send_message`, `slack_send_message_draft`, `slack_schedule_message`,
`slack_create_canvas`, `slack_update_canvas`. The agent needs none of them. It only ever
reads. And because the Slack MCP is authenticated with a *user* token, anything it sends
appears to come from **you**, not from the app.

Replace that one line with the eight read tools:

```python
allowed_tools.extend([
    "mcp__slack-mcp__slack_search_public",
    "mcp__slack-mcp__slack_search_public_and_private",
    "mcp__slack-mcp__slack_search_channels",
    "mcp__slack-mcp__slack_search_users",
    "mcp__slack-mcp__slack_read_canvas",
    "mcp__slack-mcp__slack_read_channel",
    "mcp__slack-mcp__slack_read_thread",
    "mcp__slack-mcp__slack_read_user_profile",
])
```

Canvas *reading* stays, so the warranty canvas still works. Sending does not.

This is worth more than the two minutes it costs. Capability you never intended to grant is
capability the model may eventually use — and it will look like a bug in your prompt rather
than a hole in your permissions. Grant tools by name, not by pattern.

---



## You built this

```
Customer posts in #grillmaster-support
        │
        ▼
Your Slack agent
        ├─ searches Slack (MCP)         prior threads, warranty canvas
        ├─ calls Agentforce (Agent API) warranty, defect, KB, entitlement
        └─ posts a Block Kit card       to the rep channel
        │
        ▼
Rep clicks Approve  →  customer-ready reply in the customer's thread
```

Slack Agent Kit was the orchestrator. Agentforce was the specialist. You wrote no SOQL
and no warranty logic — you gave your agent a well-described tool and let it decide.

---



## If you fall behind

You will not be the only one, and you don't need to catch up by typing faster.

**Grab a facilitator.** Raising your hand is the fastest fix available to you.

**Or skip ahead using the reference repo.** Each step has a tag, so you can jump to the end
of any step and carry on from there. If you cloned it during setup you already have it at
`~/Documents/reference`; if not, clone it now:

```bash
cd ~/Documents
git clone https://github.com/RohanSingh0/dreamforce-5930-slack-agent-kit.git reference
cd reference
git checkout step-2          # step-1 … step-5, or `main` for the finished agent

# it needs its own environment and credentials, same as your own project
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.sample .env          # add ANTHROPIC_API_KEY + the Salesforce values
slack run
```

Note this runs as a *second* Slack app, so stop your own `slack run` first — two apps
answering the same mention is confusing to watch.

Every tag passes the linter and the tests on a fresh clone, so if a checkpoint misbehaves
it is your `.env` or your Python version — not the checkpoint.

**Or just watch the rest.** The whole point of the reference repo is that you can build it
properly this evening when nobody is waiting for you. Understanding beats keeping up.

## Just want it running?

There's a separate, shorter document for that: **[QUICKSTART.md](QUICKSTART.md)** — clone the
finished agent, point it at your Slack, working in about fifteen minutes with no code to
write. It's the right starting point for facilitators, and for anyone who'd rather see it
work before understanding it.

This guide is the one to come back to afterwards. Building it a step at a time is where the
learning is, and it's yours to keep.

---

## Where things go wrong


| Symptom                                    | Cause                                             | Fix                                                 |
| ------------------------------------------ | ------------------------------------------------- | --------------------------------------------------- |
| `runtime_not_found` / `sdk_hook_not_found` | `.slack/hooks.json` calls bare `python3`          | Point it at `.venv/bin/python3`                     |
| `pip install -e ".[dev]"` fails            | Template's stale self-reference, or Python < 3.12 | Fix the `dev` extra; use 3.12+                      |
| "Administrator approval is required"       | Workspace enforces app approval                   | Set the **Default** automation rule to *Approve*    |
| `Invalid token` from Salesforce            | Wrong OAuth scope                                 | Agent API needs `sfap_api`, **not** `mcp_api`       |
| `invalid_grant` on the token call          | No Run As user on the External Client App         | Policy tab → Run As                                 |
| Agent answers without calling Salesforce   | Tool description too vague                        | Make the description specific about when to call it |
| `Maximum Logins Exceeded`                  | Minting a token per request                       | Cache the token (Step 2 does this)                  |
| Slack search returns nothing               | `search.messages` rejects bot tokens              | Needs a **user** token (`xoxp-`)                    |
| `missing_argument` on Slack API calls      | Org-scoped token                                  | Pass `team_id`                                      |
| `team_access_not_granted` on Slack calls   | On Enterprise Grid, `auth.test` returns the *enterprise* id | Use the workspace id (starts `T`) from `auth.teams.list` |
| 👀 appears, then nothing, no error ever    | The model call is hanging — see the facilitator note in the appendix | `claude -p "say OK"`; if that hangs too, it's VPN or an unavailable model |


---

