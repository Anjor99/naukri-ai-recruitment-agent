from __future__ import annotations

import json
import time
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import Response

from agent.api.document import add_document
from agent.api.ask import ask_agent
from agent.api.logging_utils import log_event
from agent.api.models import (
    AddDocumentRequest,
    AddDocumentResponse,
    AskRequest,
    AskResponse,
)


app = FastAPI()


def _new_conversation_id() -> str:
    return str(uuid.uuid4())


def _extract_request_data(
    route: str,
    body: bytes,
) -> tuple[dict[str, Any], str | None]:
    """
    Parse the incoming JSON body and return:
        (request_data, conversation_id)
    """

    if not body:
        return {}, None

    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}, None

    if not isinstance(payload, dict):
        return {}, None

    conversation_id = None

    if route == "/ask":
        conversation_id = payload.get("conversation_id")

    return payload, conversation_id


def _restore_request_body(
    request: Request,
    body: bytes,
) -> None:
    """
    Restore a body that was read by middleware so FastAPI can
    parse it normally downstream.
    """

    async def receive():
        return {
            "type": "http.request",
            "body": body,
            "more_body": False,
        }

    request._receive = receive


async def _read_response_body(response: Response) -> bytes:
    """
    Read the response body so outgoing response fields can be
    included in structured logs.

    The body is then reconstructed by the middleware.
    """

    body = b""

    if hasattr(response, "body_iterator"):
        async for chunk in response.body_iterator:
            body += chunk
    elif response.body is not None:
        body = response.body

    return body


@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):
    trace_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    route = request.url.path
    method = request.method

    request.state.trace_id = trace_id

    # Read incoming body before handing it to FastAPI.
    body = await request.body()

    request_data, conversation_id = _extract_request_data(
        route,
        body,
    )

    # First /ask request gets a conversation ID here.
    # This ID is injected into the request so run_turn()
    # receives exactly the same ID.
    if route == "/ask":
        if not conversation_id:
            conversation_id = _new_conversation_id()
            request_data["conversation_id"] = conversation_id

            body = json.dumps(
                request_data,
                ensure_ascii=False,
            ).encode("utf-8")

            request_data, _ = _extract_request_data(
                route,
                body,
            )

        request.state.conversation_id = conversation_id

    else:
        request.state.conversation_id = conversation_id

    _restore_request_body(request, body)

    # ---------------------------------------------------------
    # REQUEST EVENT
    # ---------------------------------------------------------

    log_event(
        conversation_id=conversation_id,
        trace_id=trace_id,
        event="request",
        step="input",
        method=method,
        path=route,
        query=request_data.get("query", ""),
        request_data=request_data,
    )

    status_code = 500
    response_body = b""

    try:
        response = await call_next(request)

        status_code = response.status_code

        # Read outgoing response.
        response_body = await _read_response_body(response)

        response_data: dict[str, Any] = {}

        if response_body:
            try:
                parsed = json.loads(response_body)

                if isinstance(parsed, dict):
                    response_data = parsed

            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

        # The response may contain the conversation ID.
        response_conversation_id = (
            response_data.get("conversation_id")
            or conversation_id
        )

        request.state.conversation_id = response_conversation_id

        elapsed_ms = (
            time.perf_counter() - start_time
        ) * 1000

        # -----------------------------------------------------
        # RESPONSE EVENT
        # -----------------------------------------------------

        log_event(
            conversation_id=response_conversation_id,
            trace_id=trace_id,
            event="response",
            step="api",
            elapsed_ms=round(elapsed_ms, 2),
            method=method,
            path=route,
            status_code=status_code,
            request_data=request_data,
            response_data=response_data,
            route_selected=response_data.get("route"),
            response=response_data.get("response"),
            record_id=response_data.get("record_id"),
        )

        # Reconstruct the response so the client still receives
        # the original response body.
        new_response = Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )

        new_response.headers["X-Trace-ID"] = trace_id

        return new_response

    except Exception as exc:
        elapsed_ms = (
            time.perf_counter() - start_time
        ) * 1000

        # -----------------------------------------------------
        # ERROR EVENT
        # -----------------------------------------------------

        log_event(
            conversation_id=conversation_id,
            trace_id=trace_id,
            event="error",
            step="api",
            elapsed_ms=round(elapsed_ms, 2),
            method=method,
            path=route,
            status_code=500,
            request_data=request_data,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )

        raise


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post(
    "/ask",
    response_model=AskResponse,
)
async def ask(
    request: AskRequest,
):
    return await ask_agent(request)


@app.post(
    "/add-document",
    response_model=AddDocumentResponse,
)
def add_document_endpoint(
    request: AddDocumentRequest,
):
    return add_document(request)