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
                m.get("message", "")
                for m in payload.get("messages", [])
                if m.get("message")
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
