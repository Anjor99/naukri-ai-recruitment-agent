let conversationId = null;


function getChatContainer() {

    return document.getElementById(
        "chat-messages"
    );
}


function scrollChatToBottom() {

    const container = getChatContainer();

    container.scrollTop =
        container.scrollHeight;
}


function addUserMessage(message) {

    const container =
        getChatContainer();

    const element =
        document.createElement("div");

    element.className =
        "message user-message";

    element.innerHTML = `
        <div class="message-content">
            ${escapeHtml(message)}
        </div>
    `;

    container.appendChild(element);

    scrollChatToBottom();
}


function addAgentMessage(
    message,
    metadata = {}
) {

    const container =
        getChatContainer();

    const element =
        document.createElement("div");

    element.className =
        "message agent-message";

    const route =
        metadata.route || "";

    element.innerHTML = `

        <div class="agent-avatar">
            ✦
        </div>

        <div class="message-wrapper">

            <div class="message-content">
                ${formatAgentResponse(message)}
            </div>

            ${
                route
                ? `
                    <div class="message-meta">
                        Route:
                        <strong>${escapeHtml(route)}</strong>
                    </div>
                `
                : ""
            }

        </div>
    `;

    container.appendChild(element);

    scrollChatToBottom();
}


function addLoadingMessage() {

    const container =
        getChatContainer();

    const element =
        document.createElement("div");

    element.id =
        "agent-loading";

    element.className =
        "message agent-message";

    element.innerHTML = `

        <div class="agent-avatar">
            ✦
        </div>

        <div class="message-wrapper">

            <div class="typing-indicator">

                <span></span>
                <span></span>
                <span></span>

            </div>

        </div>
    `;

    container.appendChild(element);

    scrollChatToBottom();
}


function removeLoadingMessage() {

    const loading =
        document.getElementById(
            "agent-loading"
        );

    if (loading) {
        loading.remove();
    }
}


function formatAgentResponse(text) {

    if (!text) {
        return "";
    }

    return escapeHtml(text)
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\n/g, "<br>");
}


function escapeHtml(value) {

    const div =
        document.createElement("div");

    div.textContent =
        value ?? "";

    return div.innerHTML;
}


function clearChat() {

    const container =
        getChatContainer();

    container.innerHTML = `
        <div class="welcome-message">

            <div class="welcome-icon">
                ✦
            </div>

            <h2>
                New conversation
            </h2>

            <p>
                Ask about recruitment policies,
                applications or HR processes.
            </p>

        </div>
    `;

    conversationId = null;

    document.getElementById(
        "conversation-id"
    ).textContent =
        "New conversation";

    document.getElementById(
        "route-badge"
    ).classList.add("hidden");

    updateDebugInfo({});
}


async function sendMessage(query) {

    if (!query.trim()) {
        return;
    }

    addUserMessage(query);

    addLoadingMessage();

    setChatLoading(true);

    try {

        const result =
            await API.ask(
                query,
                conversationId
            );

        const data =
            result.data;

        conversationId =
            data.conversation_id ||
            conversationId;

        document.getElementById(
            "conversation-id"
        ).textContent =
            conversationId || "Unknown";

        removeLoadingMessage();

        addAgentMessage(
            data.response ||
            "No response returned.",
            {
                route: data.route
            }
        );

        updateRoute(
            data.route
        );

        updateDebugInfo({
            route: data.route,
            traceId:
                result.headers.get(
                    "X-Trace-ID"
                ),
            recordId:
                data.record_id
        });

        if (data.record_id) {

            loadApplication(
                data.record_id
            );

        }

    } catch (error) {

        removeLoadingMessage();

        addAgentMessage(
            `Request failed: ${error.message}`
        );

    } finally {

        setChatLoading(false);
    }
}


function setChatLoading(loading) {

    const button =
        document.getElementById(
            "send-button"
        );

    const input =
        document.getElementById(
            "chat-input"
        );

    button.disabled =
        loading;

    input.disabled =
        loading;
}


function updateRoute(route) {

    const badge =
        document.getElementById(
            "route-badge"
        );

    if (!route) {

        badge.classList.add(
            "hidden"
        );

        return;
    }

    badge.textContent =
        route.toUpperCase();

    badge.className =
        `route-badge route-${route}`;
}


function updateDebugInfo({
    route,
    traceId,
    recordId
}) {

    if (route !== undefined) {

        document.getElementById(
            "debug-route"
        ).textContent =
            route || "—";
    }

    if (traceId !== undefined) {

        document.getElementById(
            "debug-trace"
        ).textContent =
            traceId || "—";
    }

    if (recordId !== undefined) {

        document.getElementById(
            "debug-record"
        ).textContent =
            recordId || "—";
    }
}