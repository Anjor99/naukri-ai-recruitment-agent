"""
agent/conversation.py

Conversation-level orchestration and persisted memory.

Each conversation is identified by a stable conversation_id.
State is loaded before a turn and saved after the turn.

Memory currently preserves:
- conversation history
- record_id from a previous application-status query
"""

import re
import uuid
from typing import Any, Dict, Optional

from agent.graph import invoke_with_timeout
from agent.memory import load_conversation, save_conversation


_RECORD_ID_PATTERN = re.compile(r"\bAPP-\d{4}\b", re.IGNORECASE)


def _new_conversation_id() -> str:
    return str(uuid.uuid4())


def _extract_record_id(query: str) -> Optional[str]:
    match = _RECORD_ID_PATTERN.search(query)

    if match:
        return match.group().upper()

    return None


async def run_turn(
    query: str,
    conversation_id: Optional[str] = None,
) -> Dict[str, Any]:

    # 1. Load all persisted conversations
    all_conversations = load_conversation()

    # 2. Create a new conversation if required
    if conversation_id is None:
        conversation_id = _new_conversation_id()

    # 3. Load previous state for this conversation
    previous_state = all_conversations.get(conversation_id, {})

    previous_history = previous_state.get("history", {})
    previous_record_id = previous_state.get("record_id")

    # 4. Prefer a record ID explicitly mentioned in the new query.
    #    Otherwise, fall back to the remembered record ID.
    current_record_id = _extract_record_id(query)
    record_id = current_record_id or previous_record_id

    # 5. Build state for this turn
    input_state = {
        "query": query,
        "conversation_id": conversation_id,
        "history": previous_history,
        "record_id": record_id,
    }

    # 6. Run the LangGraph agent
    config = {
        "configurable": {
            "thread_id": conversation_id
        }
    }

    final_state = await invoke_with_timeout(
        input_state=input_state,
        config=config,
        timeout=30
    )

    # 7. Preserve the record ID if the status tool found one
    status_result = final_state.get("status_result") or {}

    final_state["record_id"] = (
        status_result.get("record_id")
        or record_id
    )

    # 8. Append this turn to conversation history
    turn_number = len(previous_history) + 1

    updated_history = dict(previous_history)

    updated_history[str(turn_number)] = {
        "query": query,
        "route": final_state.get("route"),
        "response": final_state.get("response"),
    }

    final_state["history"] = updated_history
    final_state["conversation_id"] = conversation_id

    # 9. Persist the updated conversation
    all_conversations[conversation_id] = final_state

    save_conversation(all_conversations)

    return final_state