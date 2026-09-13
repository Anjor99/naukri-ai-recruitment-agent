from __future__ import annotations

from agent.api.models import AskRequest, AskResponse
from agent.conversation import run_turn


async def ask_agent(request: AskRequest) -> AskResponse:
    state = await run_turn(
        query=request.query,
        conversation_id=request.conversation_id,
    )

    return AskResponse(
        conversation_id=state["conversation_id"],
        route=state["route"],
        response=state["response"],
    )