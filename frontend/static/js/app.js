"use strict";


/* =========================================
   STATE
========================================= */

let conversationId =
    localStorage.getItem("naukri_conversation_id");

if (!conversationId) {
    conversationId = crypto.randomUUID();

    localStorage.setItem(
        "naukri_conversation_id",
        conversationId
    );
}


/* =========================================
   DOM
========================================= */

const chatContainer =
    document.getElementById("chat-container");

const welcomeScreen =
    document.getElementById("welcome-screen");

const messageInput =
    document.getElementById("message-input");

const sendButton =
    document.getElementById("send-btn");

const newChatButton =
    document.getElementById("new-chat-btn");

const conversationLabel =
    document.getElementById("conversation-label");


/* =========================================
   INITIALIZATION
========================================= */

conversationLabel.textContent =
    "Conversation active";


/* =========================================
   SEND MESSAGE
========================================= */

async function sendMessage(customMessage = null) {

    const message =
        customMessage !== null
            ? customMessage.trim()
            : messageInput.value.trim();

    if (!message) {
        return;
    }

    if (customMessage === null) {
        messageInput.value = "";
        autoResizeTextarea();
    }

    hideWelcomeScreen();

    addUserMessage(message);

    setLoading(true);

    const typingElement = addTypingIndicator();

    try {

        const response = await fetch(
            "/ask",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    query: message,
                    conversation_id: conversationId
                })
            }
        );


        removeTypingIndicator(typingElement);


        if (!response.ok) {

            let errorMessage =
                `Request failed (${response.status}).`;

            try {
                const errorData =
                    await response.json();

                if (errorData.detail) {
                    errorMessage =
                        errorData.detail;
                }
            } catch (_) {
                // Keep default error message.
            }

            addErrorMessage(errorMessage);

            return;
        }


        const data =
            await response.json();


        /*
         * The backend may return a conversation ID.
         * If it does, keep using it.
         */

        if (data.conversation_id) {

            conversationId =
                data.conversation_id;

            localStorage.setItem(
                "naukri_conversation_id",
                conversationId
            );
        }


        renderAgentResponse(data);


    } catch (error) {

        removeTypingIndicator(typingElement);

        console.error(
            "Request error:",
            error
        );

        addErrorMessage(
            "Unable to connect to the AI agent. Please try again."
        );

    } finally {

        setLoading(false);
    }
}


/* =========================================
   RENDER AGENT RESPONSE
========================================= */

function renderAgentResponse(data) {

    /*
     * Your API's main answer.
     */

    const responseText =
        data.response ||
        data.message ||
        "The agent returned an empty response.";

    addAssistantMessage(
        responseText
    );


    /*
     * If your API exposes an application
     * record ID, render a status card.
     */

    if (
        data.record_id &&
        (
            data.status ||
            data.expected_salary_inr
        )
    ) {

        addStatusCard(data);
    }


    /*
     * If your API eventually exposes
     * retrieval metadata, the UI can show it.
     *
     * These fields are optional and therefore
     * won't break the frontend if absent.
     */

    if (
        data.source ||
        data.similarity ||
        data.top_similarity
    ) {

        addGroundingInfo(data);
    }
}


/* =========================================
   USER MESSAGE
========================================= */

function addUserMessage(message) {

    const row =
        document.createElement("div");

    row.className =
        "message-row user";


    const bubble =
        document.createElement("div");

    bubble.className =
        "message user";

    bubble.textContent =
        message;


    row.appendChild(bubble);

    chatContainer.appendChild(row);

    scrollToBottom();
}


/* =========================================
   ASSISTANT MESSAGE
========================================= */

function addAssistantMessage(message) {

    const row =
        document.createElement("div");

    row.className =
        "message-row assistant";


    const bubble =
        document.createElement("div");

    bubble.className =
        "message assistant";

    /*
     * textContent is intentional.
     *
     * We don't insert backend responses as HTML.
     * This prevents the frontend from rendering
     * arbitrary HTML returned by the API.
     */

    bubble.textContent =
        message;


    row.appendChild(bubble);

    chatContainer.appendChild(row);

    scrollToBottom();
}


/* =========================================
   STATUS CARD
========================================= */

function addStatusCard(data) {

    const row =
        document.createElement("div");

    row.className =
        "message-row assistant";


    const card =
        document.createElement("div");

    card.className =
        "status-card";


    const header =
        document.createElement("div");

    header.className =
        "status-card-header";

    header.textContent =
        `Application ${data.record_id}`;


    const body =
        document.createElement("div");

    body.className =
        "status-card-body";


    if (data.status) {

        body.appendChild(
            createStatusField(
                "Status",
                data.status
            )
        );
    }


    if (
        data.expected_salary_inr !== undefined &&
        data.expected_salary_inr !== null
    ) {

        body.appendChild(
            createStatusField(
                "Expected Salary",
                formatCurrency(
                    data.expected_salary_inr
                )
            )
        );
    }


    if (data.days_since_created !== undefined) {

        body.appendChild(
            createStatusField(
                "Application Age",
                `${data.days_since_created} days`
            )
        );
    }


    card.appendChild(header);
    card.appendChild(body);

    row.appendChild(card);

    chatContainer.appendChild(row);

    scrollToBottom();
}


function createStatusField(
    label,
    value
) {

    const field =
        document.createElement("div");

    field.className =
        "status-field";


    const labelElement =
        document.createElement("span");

    labelElement.textContent =
        label;


    const valueElement =
        document.createElement("span");

    valueElement.textContent =
        value;


    field.appendChild(labelElement);
    field.appendChild(valueElement);

    return field;
}


/* =========================================
   GROUNDING INFO
========================================= */

function addGroundingInfo(data) {

    const row =
        document.createElement("div");

    row.className =
        "message-row assistant";


    const box =
        document.createElement("div");

    box.className =
        "status-card";


    const header =
        document.createElement("div");

    header.className =
        "status-card-header";

    header.textContent =
        "✓ Retrieval information";


    const body =
        document.createElement("div");

    body.className =
        "status-card-body";


    if (data.source) {

        body.appendChild(
            createStatusField(
                "Source",
                data.source
            )
        );
    }


    const similarity =
        data.similarity ??
        data.top_similarity;


    if (similarity !== undefined) {

        body.appendChild(
            createStatusField(
                "Similarity",
                Number(similarity).toFixed(3)
            )
        );
    }


    box.appendChild(header);
    box.appendChild(body);

    row.appendChild(box);

    chatContainer.appendChild(row);

    scrollToBottom();
}


/* =========================================
   TYPING INDICATOR
========================================= */

function addTypingIndicator() {

    const row =
        document.createElement("div");

    row.className =
        "message-row assistant";


    const indicator =
        document.createElement("div");

    indicator.className =
        "typing-indicator";


    for (let i = 0; i < 3; i++) {

        const dot =
            document.createElement("span");

        indicator.appendChild(dot);
    }


    row.appendChild(indicator);

    chatContainer.appendChild(row);

    scrollToBottom();

    return row;
}


function removeTypingIndicator(element) {

    if (element && element.parentNode) {

        element.parentNode.removeChild(
            element
        );
    }
}


/* =========================================
   ERROR
========================================= */

function addErrorMessage(message) {

    const row =
        document.createElement("div");

    row.className =
        "message-row assistant";


    const error =
        document.createElement("div");

    error.className =
        "error-message";

    error.textContent =
        message;


    row.appendChild(error);

    chatContainer.appendChild(row);

    scrollToBottom();
}


/* =========================================
   NEW CHAT
========================================= */

function startNewConversation() {

    conversationId =
        crypto.randomUUID();

    localStorage.setItem(
        "naukri_conversation_id",
        conversationId
    );


    /*
     * Clear UI.
     */

    chatContainer.innerHTML = "";

    chatContainer.appendChild(
        createWelcomeScreen()
    );


    conversationLabel.textContent =
        "New conversation";

    messageInput.focus();
}


function createWelcomeScreen() {

    const wrapper =
        document.createElement("div");

    wrapper.className =
        "welcome-screen";


    wrapper.innerHTML = `
        <div class="welcome-icon">✦</div>

        <h2>How can I help you?</h2>

        <p>
            Ask about recruitment policies,
            hiring processes, or check an
            application status.
        </p>
    `;

    return wrapper;
}


/* =========================================
   WELCOME
========================================= */

function hideWelcomeScreen() {

    if (welcomeScreen) {

        welcomeScreen.remove();
    }
}


/* =========================================
   LOADING
========================================= */

function setLoading(isLoading) {

    sendButton.disabled =
        isLoading;

    messageInput.disabled =
        isLoading;
}


/* =========================================
   TEXTAREA
========================================= */

function autoResizeTextarea() {

    messageInput.style.height =
        "auto";

    messageInput.style.height =
        Math.min(
            messageInput.scrollHeight,
            120
        ) + "px";
}


/* =========================================
   HELPERS
========================================= */

function scrollToBottom() {

    requestAnimationFrame(() => {

        chatContainer.scrollTo({
            top: chatContainer.scrollHeight,
            behavior: "smooth"
        });

    });
}


function formatCurrency(value) {

    const number =
        Number(value);

    if (Number.isNaN(number)) {
        return String(value);
    }

    return new Intl.NumberFormat(
        "en-IN",
        {
            style: "currency",
            currency: "INR",
            maximumFractionDigits: 0
        }
    ).format(number);
}


/* =========================================
   EVENT LISTENERS
========================================= */

sendButton.addEventListener(
    "click",
    () => sendMessage()
);


messageInput.addEventListener(
    "keydown",
    (event) => {

        /*
         * Enter = send
         *
         * Shift + Enter = new line
         */

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendMessage();
        }
    }
);


messageInput.addEventListener(
    "input",
    autoResizeTextarea
);


newChatButton.addEventListener(
    "click",
    startNewConversation
);


/*
 * Sidebar quick questions.
 */

document
    .querySelectorAll(".suggestion")
    .forEach(button => {

        button.addEventListener(
            "click",
            () => {

                sendMessage(
                    button.dataset.query
                );

            }
        );
    });


/*
 * Welcome screen example cards.
 */

document
    .querySelectorAll(".example-card")
    .forEach(button => {

        button.addEventListener(
            "click",
            () => {

                sendMessage(
                    button.dataset.query
                );

            }
        );
    });