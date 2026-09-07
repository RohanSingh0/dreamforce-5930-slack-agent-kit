# GrillMaster Agent — Dreamforce '26 session 5930

Reference code for **Build an Agent Using Slack Agent Kit**.

A Slack agent that takes a customer's complaint, searches Slack history for prior context,
asks a Salesforce Agentforce agent what the record system knows about warranty and defects,
and posts a resolution card into an internal channel for a human to approve before the
customer ever sees a reply.

You will build this in the session. This repo is here so that **falling behind is not fatal.**

**Start here: [QUICKSTART.md](QUICKSTART.md)** — clone this, point it at your Slack, working
in about fifteen minutes with no code to write.

Then **[EXERCISE_GUIDE.md](EXERCISE_GUIDE.md)** if you want to build it yourself a step at a
time, which is where the learning is.

---

## Catching up mid-session

There is one commit per exercise step. If you get lost, jump to the end of any step:

```bash
git checkout step-2      # end of step 2, ready to start step 3
```

| Tag | You have | Guide step |
|---|---|---|
| `step-1` | Scaffolded agent, template fixes applied | 1 · Scaffold |
| `step-2` | Agentforce research tool wired in | 2 · Delegate research |
| `step-3` | System prompt with hard rules on facts | 3 · Shape behaviour |
| `step-4` | Resolution card posted as a tool | 4 · Build the interface |
| `step-5` | Rep review channel and Approve button | 5 · Human in the loop |

Every tag passes `ruff check .` and `pytest`, so if something is broken it is your
environment and not the checkpoint.

To get back to the finished build: `git checkout main`.

---

## Setup

You need **Python 3.12+**, the [Slack CLI](https://tools.slack.dev/slack-cli/), and your
own Anthropic API key from [console.anthropic.com](https://console.anthropic.com). A Claude
Code or Cursor subscription is *not* the same thing and will not work here.

```bash
git clone https://github.com/RohanSingh0/dreamforce-5930-slack-agent-kit.git
cd dreamforce-5930-slack-agent-kit
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.sample .env          # then fill it in
slack run
```

`.env.sample` lists every value you need. The four Salesforce values point at the shared
workshop org and are handed out in the session — they are deliberately not in this repo.

If `slack run` uses the wrong Python, check `.slack/hooks.json` points at
`.venv/bin/python3`.

---

## How it fits together

```
customer posts in #grillmaster-support
        │
        ▼
  @mention listener  ──►  Claude Agent SDK loop
                              │
                              ├─ Slack MCP        search prior threads
                              ├─ Agentforce tool  warranty, defect, KB, entitlement
                              └─ card tool        post to #grillmaster-reps
                                                       │
                              customer's thread ◄── Approve
```

The split across two channels is the point. Batch codes, entitlement decisions and prior
case history stay in the internal channel; only the approved reply reaches the customer.
That is why the card's buttons carry the customer's channel and thread id — the human
clicks Approve in one place and the answer lands in another.

The agent is told, in its system prompt, that warranty status, defect status, dates, serial
numbers, article ids and part numbers may come **only** from the Agentforce tool. A model
that guesses these convincingly is worse than one that says it does not know.

---

## Layout

```
agent/
  casey.py                  system prompt, tool registry, the reasoning loop
  cards.py                  Block Kit for the resolution card
  tools/
    agentforce.py           Agent API: token, session, message
    resolution_card.py      posts the card, routes to the rep channel
listeners/
  events/app_mentioned.py   entry point for @mentions
  actions/
    resolution_buttons.py   Approve
```
