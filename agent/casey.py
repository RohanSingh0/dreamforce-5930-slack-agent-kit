from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    create_sdk_mcp_server,
)
from claude_agent_sdk.types import McpHttpServerConfig

from agent.context import casey_deps_var
from agent.deps import CaseyDeps
from agent.tools import (
    add_emoji_reaction_tool,
    ask_agentforce_tool,
    check_system_status_tool,
    create_support_ticket_tool,
    lookup_user_permissions_tool,
    mark_resolved_tool,
    post_resolution_card_tool,
    search_knowledge_base_tool,
    trigger_password_reset_tool,
)

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

casey_tools_server = create_sdk_mcp_server(
    name="casey-tools",
    version="1.0.0",
    tools=[
        add_emoji_reaction_tool,
        ask_agentforce_tool,
        post_resolution_card_tool,
        check_system_status_tool,
        create_support_ticket_tool,
        lookup_user_permissions_tool,
        mark_resolved_tool,
        search_knowledge_base_tool,
        trigger_password_reset_tool,
    ],
)

SLACK_MCP_URL = "https://mcp.slack.com/mcp"

CASEY_TOOLS = [
    "add_emoji_reaction",
    "ask_agentforce_about_product_issue",
    "post_resolution_card",
    "check_system_status",
    "create_support_ticket",
    "lookup_user_permissions",
    "mark_resolved",
    "search_knowledge_base",
    "trigger_password_reset",
]


async def run_casey_agent(
    text: str,
    session_id: str | None = None,
    deps: CaseyDeps | None = None,
) -> tuple[str, str | None]:
    """Run the Casey agent with the given text and optional session for context.

    Args:
        text: The user's message text.
        session_id: Optional session ID to resume a previous conversation.
        deps: Optional dependencies for tools that need Slack API access.

    Returns:
        A tuple of (response_text, new_session_id).
    """
    if deps:
        casey_deps_var.set(deps)

    mcp_servers: dict = {"casey-tools": casey_tools_server}
    allowed_tools = list(CASEY_TOOLS)

    if deps and deps.user_token:
        mcp_servers["slack-mcp"] = McpHttpServerConfig(
            type="http",
            url=SLACK_MCP_URL,
            headers={"Authorization": f"Bearer {deps.user_token}"},
        )
        allowed_tools.append("mcp__slack-mcp__*")

    options = ClaudeAgentOptions(
        system_prompt=CASEY_SYSTEM_PROMPT,
        mcp_servers=mcp_servers,
        allowed_tools=allowed_tools,
        permission_mode="bypassPermissions",
    )

    if session_id:
        options.resume = session_id

    response_parts: list[str] = []
    new_session_id: str | None = None

    async with ClaudeSDKClient(options) as client:
        await client.query(text)

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_parts.append(block.text)
            if isinstance(message, ResultMessage):
                new_session_id = message.session_id

    response_text = "\n".join(response_parts) if response_parts else ""
    return response_text, new_session_id
