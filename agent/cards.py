def build_resolution_card(
    *,
    customer_name,
    draft_message,
    product_summary="",
    warranty_status="",
    defect_status="",
    knowledge_article="",
    entitlement="",
) -> list[dict]:
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Resolution ready for review"},
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"*Customer:* {customer_name}  ·  {product_summary}",
                }
            ],
        },
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

    blocks.append(
        {
            "type": "actions",
            "block_id": "resolution_actions",
            "elements": [
                {
                    "type": "button",
                    "action_id": "resolution_approve",
                    "style": "primary",
                    "text": {"type": "plain_text", "text": "Approve & Send"},
                    "value": "ok",
                },
                {
                    "type": "button",
                    "action_id": "resolution_edit",
                    "text": {"type": "plain_text", "text": "Edit"},
                    "value": "ok",
                },
            ],
        }
    )
    return blocks
