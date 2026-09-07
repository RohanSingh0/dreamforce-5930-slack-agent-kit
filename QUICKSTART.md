# Quickstart — a working agent in about fifteen minutes

**Session 5930 · Build an Agent Using Slack Agent Kit**

This is the short path. You clone the finished agent, point it at your own Slack, and watch
it work. No code to write.

**Who this is for.** Facilitators getting a working environment before the session, and
anyone who wants to see it running before they understand it. If you'd rather build it a
piece at a time — which is where the learning is — use the full **exercise guide** instead:
same code, five steps, about forty minutes. Doing this first and that afterwards is a good
order, and it's what facilitators should do.

Written for someone who can follow commands in a terminal. Every command is exact, and every
stage tells you what you should see before you move on.

---

## What you'll end up with

You post a customer complaint in Slack. The agent notices it, searches Slack for related
history, asks a Salesforce Agentforce agent what the records say about warranty and defects,
and posts back a card with its findings and a draft reply for a human to approve.

---

## Before you start — three things

Run these three commands. They take twenty seconds and save you from finding a problem
halfway through.

```bash
python3 --version
slack version
echo $ANTHROPIC_API_KEY
```

| Command | You want | If not |
|---|---|---|
| `python3 --version` | `3.12` or higher | See *Python is too old* below |
| `slack version` | any version number | `curl -fsSL https://downloads.slack-edge.com/slack-cli/install.sh \| bash` |
| `echo $ANTHROPIC_API_KEY` | something starting `sk-ant-` | Get one at [console.anthropic.com](https://console.anthropic.com) → Settings → API Keys. It needs a payment method; a workshop's use costs cents. |

You also need a **Slack workspace where you are an admin**. You'll be installing an app, and
a corporate workspace will refuse. If you don't have one, creating a free workspace takes two
minutes.

> **Python is too old.** macOS ships 3.9. You don't need admin rights to fix it:
>
> ```bash
> curl -fsSL https://astral.sh/uv/install.sh | sh
> uv python install 3.12
> ```
>
> After that, use `python3.12` wherever this guide says it.

You'll also need the **four Salesforce values** from your session handout. They point at a
shared org that already has the data and the Agentforce agent in it — there is nothing for
you to set up on the Salesforce side.

---

## 1 · Get the code

Open a terminal. In VS Code that's **Terminal → New Terminal**, or **Ctrl+`**.

```bash
cd ~/Documents
git clone https://github.com/RohanSingh0/dreamforce-5930-slack-agent-kit.git grillmaster
cd grillmaster
code .
```

**You should see** a `grillmaster` folder open in your editor with `agent/` and `listeners/`
directories inside it.

---

## 2 · Install it

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**You should see** a long list of installed packages ending in a success line. Somewhere in
that list are `slack-bolt` and `claude-agent-sdk`.

If it complains about `setup.py` or editable mode, your virtual environment is on an old
Python. Delete it with `rm -rf .venv` and redo this step using `python3.12` explicitly.

---

## 3 · Connect the Slack CLI to your workspace

```bash
slack login
```

This one is fiddlier than it looks, so step by step:

1. The terminal prints a line starting `/slackauthticket` and then waits. **Copy that whole
   line**, including the `/`.
2. Open Slack, go to **your own workspace**, and click into any channel or your own DMs.
3. Paste the line into the message box and press Enter. Slack runs it as a command — nothing
   is posted where others can see it.
4. Click **Confirm** in the dialog that appears.
5. Slack shows you a **challenge code**. Copy it.
6. Paste it into the terminal that's still waiting, and press Enter.

**You should see** a confirmation naming your workspace. If it says the ticket expired, just
run `slack login` again — they don't last long.

---

## 4 · Start the app

```bash
slack run
```

The first time, this creates the Slack app for you. Answer the prompts:

- **Create a new app** → yes
- **Which workspace** → yours
- **Grant access** → pick the specific workspace, not the whole organisation

**You should see** `⚡️ Bolt app is running!` Leave this terminal alone from now on — this
*is* your agent running. Everything else happens in a second terminal or in Slack.

> **"Administrator approval is required"** means you aren't an admin of that workspace. No
> amount of retrying helps; use a workspace you own.

---

## 5 · Make a channel and invite the agent

In Slack:

1. Create a **public** channel called **`#grillmaster-support`**
2. In that channel, type `/invite @grillmaster-agent` and press Enter

**You should see** the app join the channel.

---

## 6 · Get your Slack user token

The agent searches Slack, and Slack's search requires a *user* token. Without it the agent
quietly has no search ability at all.

Open a **second terminal** so you don't stop the app:

```bash
cd ~/Documents/grillmaster
slack app settings
```

Your app's settings open in a browser. Then:

1. Left sidebar → **Settings → Install App**
2. Copy the **User OAuth Token** — the one starting **`xoxp-`**

> Take the `xoxp-` token, **not** the Bot token starting `xoxb-`. Slack's search rejects bot
> tokens, and the failure is silent rather than obvious.

---

## 7 · Fill in your settings

```bash
cp .env.sample .env
```

Open `.env` in your editor. It's a hidden file, so if the file tree won't show it, press
**Cmd+P** (Ctrl+P on Windows/Linux), type `.env`, and pick it.

Fill in these six values. No quotes, and no spaces around the `=`:

```bash
ANTHROPIC_API_KEY=sk-ant-...        # yours
SLACK_USER_TOKEN=xoxp-...           # from step 6

SF_MY_DOMAIN=...                    # these four are on your
SF_AGENT_ID=...                     # session handout — paste
SF_CONSUMER_KEY=...                 # them exactly as printed
SF_CONSUMER_SECRET=...
```

Leave everything else in the file alone.

Now restart the app so it reads them. In the first terminal press **Ctrl+C**, then:

```bash
slack run
```

---

## 8 · Try it

In `#grillmaster-support`, post this. Type `@grill` and pick the app from the autocomplete so
it becomes a real mention — pasting the plain text won't trigger anything.

```
@grillmaster-agent My new grill's igniter won't light and one of the burners
isn't heating evenly. I bought it two weeks ago — can someone help me get this
fixed or replaced? — Jordan Reyes
```

**Keep the `— Jordan Reyes` at the end.** That's how the agent knows which customer to look
up in Salesforce. Without it there's nothing to search for.

**You should see**, in order:

1. A 👀 reaction within a second or two
2. A "thinking" indicator
3. A card in the thread with the customer's grill, its warranty status, a known defect, a
   knowledge article and a recommendation — and buttons to approve or edit

In the terminal you should see two lines proving both integrations are live:

```
Slack MCP registered ...
Agentforce answered in 8.2s (attempt 1)
```

That's a working agent. Everything below is optional.

---

## Optional · The full split-channel demo

By default the card appears in the same thread as the customer's message. In the real design
it goes to a private channel for a rep to approve, so the customer never sees the internal
detail.

1. Create a second public channel, **`#grillmaster-reps`**, and `/invite @grillmaster-agent`
2. Right-click that channel → **View channel details** → the channel ID is at the bottom. It
   starts with `C`.
3. Put it in `.env` as `REP_CHANNEL=C...`
4. Restart `slack run`

Now posting as a customer gets a brief acknowledgement in the thread, while the full card
goes to `#grillmaster-reps`. Click **Approve & Send** there and the reply appears in the
customer's thread.

## Optional · Give it Slack history to find

Your channels are empty, so the agent's Slack search finds nothing and the card carries only
what Salesforce knew. This adds a little history to both channels:

```bash
python3 scripts/seed_slack_history.py
```

It only adds messages, never deletes, and won't run twice in the same channel.

Post the message again afterwards and the card gains a *From Slack* line. The interesting
part: it will now recommend replacing **two** parts rather than one, because a thread in
`#grillmaster-reps` explains that the same fault also causes the uneven heating. That
reasoning exists nowhere in Salesforce — it came from the conversation.

---

## When something doesn't work

| What you see | What's wrong |
|---|---|
| `invalid_app_directory` | You're in the wrong folder. `cd` into the cloned repo. Don't run `slack init`. |
| `runtime_not_found` | Your `.venv` is missing or on the wrong Python. Redo step 2. |
| Administrator approval required | You aren't an admin of that workspace. Use one you own. |
| 👀 appears, then nothing, ever | The model call is failing. Check `ANTHROPIC_API_KEY` is set, then run `claude -p "say OK"` — if that hangs too, the problem is your model access, not this project. |
| Card says no product found | The `— Jordan Reyes` signature is missing from your message. |
| Card has no *From Slack* line | Expected until you run the seeding script. |
| `Invalid token` from Salesforce | Re-check the four handout values for a stray space or line break. |

If you get properly stuck, the full exercise guide has a longer troubleshooting table with
the underlying causes.

---

## Facilitators inside Salesforce — read this one

If your `claude` CLI routes through the **internal LLM Gateway** rather than a direct
Anthropic key, you will hit a failure that looks like nothing at all: 👀 appears, the thinking
indicator shows, and then silence. No error, no timeout, no log line.

The cause is that the gateway serves only the models your team is entitled to, and an
unavailable model **hangs rather than returning an error**. The SDK's default model was
withdrawn without notice during this project's build, which is exactly how we found this.

Diagnose it in one second:

```bash
claude -p "say OK"
```

If that answers, your model access is fine and the problem is elsewhere. If it hangs, either
your VPN is down — the gateway is not reachable from outside the network — or the default
model is no longer served.

To pin a model you know works, add two lines to `agent/casey.py` immediately after `options`
is created:

```python
    model = os.environ.get("CLAUDE_MODEL", "").strip()
    if model:
        options.model = model
```

Then put `CLAUDE_MODEL=claude-sonnet-5` in `.env` and restart. To see what your team can
actually use — the gateway answers in about a second — run:

```bash
KEY=$(jq -r .apiKeyHelper ~/.claude/settings.json | sh)
BASE=$(jq -r .env.ANTHROPIC_BASE_URL ~/.claude/settings.json)
curl -s -H "x-api-key: $KEY" -H "anthropic-version: 2023-06-01" \
  "$BASE/v1/models" | jq -r '.data[].id' | grep claude
```

Note the model names are **versioned** — `claude-haiku-4-5-20251001`, not
`claude-haiku-4-5`. A near-miss name hangs in exactly the same way a withdrawn model does,
which makes a typo indistinguishable from a permissions problem.

None of this affects attendees using a key from console.anthropic.com. Worth knowing before
you help someone whose agent has gone quiet: ask which they're using first.
