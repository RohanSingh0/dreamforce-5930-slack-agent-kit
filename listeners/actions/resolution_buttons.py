import json


async def handle_resolution_approve(ack, body, client, context, logger):
    await ack()
    origin = json.loads(body["actions"][0]["value"])
    blocks = body["message"]["blocks"]
    draft = next(
        b["text"]["text"] for b in blocks if b.get("type") == "section" and "text" in b
    )

    # the customer-facing reply, into the customer's own thread
    await client.chat_postMessage(
        channel=origin["c"], thread_ts=origin["t"], text=draft
    )

    # stamp the card so the team can see it was handled
    kept = [b for b in blocks if b.get("block_id") != "resolution_actions"]
    kept.append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f":white_check_mark: Approved by <@{context.user_id}>",
                }
            ],
        }
    )
    await client.chat_update(
        channel=body["channel"]["id"],
        ts=body["message"]["ts"],
        blocks=kept,
        text="Approved",
    )
