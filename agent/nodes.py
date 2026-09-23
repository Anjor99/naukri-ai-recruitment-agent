from agent.router import route_query, _RECORD_ID_PATTERN, PossibleRoutes
from agent.tools import check_job_application_status
from agent.state import AgentState
from agent.field_selector import _field_selector
from agent.helpers import _format_status_response
from rag.vector_store import VectorStore
from rag.generator import GroundedGenerator
from rag.embeddings import EmbeddingModel

def router_node(state: AgentState) -> dict:
    """Route the query to the appropriate handler.

    Args:
        state (AgentState): The current agent state.

    Returns:
        dict: The updated agent state with route.
    """
    route = route_query(
        state["query"],
        state.get("record_id")
    ).value
    
    return {
        "route": route
    }
    
def status_node(state: AgentState) -> dict:
    match = _RECORD_ID_PATTERN.search(state["query"])

    if match:
        record_id = match.group().upper()
    else:
        record_id = state.get("record_id")

    if not record_id:
        return {
            "status_result": {
                "record_id": None,
                "found": False,
                "error": (
                    "No application record ID was provided "
                    "or remembered."
                ),
            }
        }

    result = check_job_application_status(record_id)

    return {
        "status_result": result,
        "record_id": record_id,
    }
    
def field_selector_node(state: AgentState) -> dict:
    result = _field_selector.classify(
        state["query"]
    )

    return {
        "requested_fields": [
            match.field.value
            for match in result.requested_fields
        ],
        "unsupported_fields": [
            item.clause
            for item in result.unsupported_fields
        ],
    }
    
    
async def rag_node(state: AgentState) -> dict:
    """Retrieve grounded information for the user's query."""

    vector_store = VectorStore(EmbeddingModel())
    grounded_generator = GroundedGenerator(vector_store)

    result = grounded_generator.generate(
        query=state["query"],
        collection=vector_store.create_collection("fixed_size_collection"),
        top_k=5,
    )

    return {
        "rag_result": result
    }
    
def unknown_node(state: AgentState) -> dict:
    """Safe response for unknown intent"""
    return {
        "unknown_result": "Unable to classify User intent with confidence"
    }


def response_node(state: AgentState) -> dict:
    """Generate the final response based on the selected route."""

    if state["route"] == PossibleRoutes.STATUS.value:
        return {
            "response": _format_status_response(
                state["status_result"],
                state.get("requested_fields", ["status"]),
                state.get("unsupported_fields", []),
            )
        }
    elif state["route"] == PossibleRoutes.UNKNOWN.value:
        return {
            "response": (
                f"{state['unknown_result']}"
            )
        }

    return {
        "response": (
            f"{state['rag_result']}"
        )
    }