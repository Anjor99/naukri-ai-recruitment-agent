from agent.router import route_query, _RECORD_ID_PATTERN, PossibleRoutes
from agent.tools import check_job_application_status
from agent.state import AgentState
from agent.field_selector import select_fields
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
    """Query application data using the current or remembered record ID."""

    match = _RECORD_ID_PATTERN.search(state["query"])

    if match:
        record_id = match.group().upper()
    else:
        record_id = state.get("record_id")

    if not record_id:
        return {
            "status_result": {
                "record_id": None,
                "error": "No application record ID was provided or remembered."
            }
        }

    record = check_job_application_status(record_id)

    return {
        "status_result": record,
        "record_id": record_id,
    }
    
def field_selector_node(state: AgentState) -> dict:
    """Determine which application fields the user requested."""

    fields = select_fields(state["query"])

    # Generic status/application query
    if not fields:
        fields = ["status"]

    return {
        "requested_fields": fields
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


def response_node(state: AgentState) -> dict:
    """Generate the final response based on the selected route."""

    if state["route"] == PossibleRoutes.STATUS.value:
        return {
            "response": _format_status_response(
                state["status_result"],
                state.get("requested_fields", ["status"]),
            )
        }

    return {
        "response": (
            f"Following is related information for your query : "
            f"{state['rag_result']}"
        )
    }