document.addEventListener(
    "DOMContentLoaded",
    () => {

        initializeFrontend();

    }
);


async function initializeFrontend() {

    setupChat();

    setupSuggestions();

    setupApplicationSearch();

    setupNewConversation();

    setupGraphRefresh();

    setupSidebarToggle();

    setupViewTabs();

    await Promise.all([
        loadKnowledgeBase(),
        loadGraph(),
        checkHealth()
    ]);

}


function setupChat() {

    const form =
        document.getElementById(
            "chat-form"
        );

    const input =
        document.getElementById(
            "chat-input"
        );


    form.addEventListener(
        "submit",
        event => {

            event.preventDefault();

            const query =
                input.value.trim();

            if (!query) {
                return;
            }

            input.value = "";

            autoResizeTextarea(
                input
            );

            sendMessage(
                query
            );
        }
    );


    input.addEventListener(
        "keydown",
        event => {

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                form.requestSubmit();
            }
        }
    );


    input.addEventListener(
        "input",
        () => {

            autoResizeTextarea(
                input
            );
        }
    );
}


function setupSuggestions() {

    document
        .querySelectorAll(
            ".suggestion-button"
        )
        .forEach(
            button => {

                button.addEventListener(
                    "click",
                    () => {

                        sendMessage(
                            button.dataset.query
                        );
                    }
                );
            }
        );
}


function setupApplicationSearch() {

    document
        .getElementById(
            "application-search-btn"
        )
        .addEventListener(
            "click",
            searchApplication
        );


    document
        .getElementById(
            "application-id-input"
        )
        .addEventListener(
            "keydown",
            event => {

                if (
                    event.key === "Enter"
                ) {

                    event.preventDefault();

                    searchApplication();
                }
            }
        );
}


function setupNewConversation() {

    document
        .getElementById(
            "new-chat-btn"
        )
        .addEventListener(
            "click",
            clearChat
        );
}


function setupSidebarToggle() {

    const toggleButton =
        document.getElementById(
            "sidebar-toggle-btn"
        );

    const sidebar =
        document.getElementById(
            "app-sidebar"
        );

    const backdrop =
        document.getElementById(
            "sidebar-backdrop"
        );

    if (
        !toggleButton ||
        !sidebar ||
        !backdrop
    ) {
        return;
    }

    const closeSidebar = () => {

        sidebar.classList.remove(
            "open"
        );

        backdrop.classList.remove(
            "visible"
        );

        toggleButton.setAttribute(
            "aria-expanded",
            "false"
        );
    };

    const toggleSidebar = () => {

        const isOpen =
            sidebar.classList.toggle(
                "open"
            );

        backdrop.classList.toggle(
            "visible",
            isOpen
        );

        toggleButton.setAttribute(
            "aria-expanded",
            String(isOpen)
        );
    };

    toggleButton.addEventListener(
        "click",
        toggleSidebar
    );

    backdrop.addEventListener(
        "click",
        closeSidebar
    );

    // Close the drawer automatically once the user picks
    // something inside it, so it doesn't sit open over the chat.
    sidebar.addEventListener(
        "click",
        event => {

            if (
                event.target.closest(
                    ".kb-button"
                ) ||
                event.target.closest(
                    "#application-search-btn"
                )
            ) {

                closeSidebar();
            }
        }
    );
}


function setupViewTabs() {

    const tabs =
        document.querySelectorAll(
            ".view-tab"
        );

    const panels = {
        chat:
            document.getElementById(
                "chat-view-panel"
            ),
        graph:
            document.getElementById(
                "graph-view-panel"
            )
    };

    if (
        !tabs.length ||
        !panels.chat ||
        !panels.graph
    ) {
        return;
    }

    const activateView = view => {

        tabs.forEach(
            tab => {

                const isActive =
                    tab.dataset.view === view;

                tab.classList.toggle(
                    "active",
                    isActive
                );

                tab.setAttribute(
                    "aria-selected",
                    String(isActive)
                );
            }
        );

        Object.entries(panels).forEach(
            ([key, panel]) => {

                panel.classList.toggle(
                    "hidden",
                    key !== view
                );
            }
        );

        // The graph panel is laid out while hidden
        // (display: none reports zero size), so its
        // connecting lines need to be redrawn once it's
        // actually visible and has real dimensions.
        if (
            view === "graph" &&
            typeof refreshGraphLayout ===
            "function"
        ) {

            refreshGraphLayout();
        }
    };

    tabs.forEach(
        tab => {

            tab.addEventListener(
                "click",
                () => {

                    activateView(
                        tab.dataset.view
                    );
                }
            );
        }
    );


    activateView("chat");
}


function setupGraphRefresh() {

    document
        .getElementById(
            "refresh-graph-btn"
        )
        .addEventListener(
            "click",
            loadGraph
        );
}


async function checkHealth() {

    const indicator =
        document.getElementById(
            "status-indicator"
        );

    const text =
        document.getElementById(
            "system-status-text"
        );

    try {

        const result =
            await API.health();

        if (
            result.data?.status ===
            "ok"
        ) {

            indicator.classList.add(
                "online"
            );

            text.textContent =
                "System operational";

        } else {

            throw new Error(
                "Unexpected health response"
            );
        }

    } catch {

        indicator.classList.remove(
            "online"
        );

        indicator.classList.add(
            "offline"
        );

        text.textContent =
            "System unavailable";
    }
}


function autoResizeTextarea(
    textarea
) {

    textarea.style.height =
        "auto";

    textarea.style.height =
        `${Math.min(
            textarea.scrollHeight,
            160
        )}px`;
}