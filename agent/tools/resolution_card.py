import json
import os

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
