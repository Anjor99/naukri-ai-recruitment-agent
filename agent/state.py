from typing import TypedDict

class AgentState(TypedDict):
    """
    State carried through the LangGraph agent.
    """
    query: str
    route: str
    rag_result: str
    unknown_result: str
    status_result: dict
    response: str
    history: dict
    conversation_id: str
    record_id: str
    requested_fields: list[str]