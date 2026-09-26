async function loadKnowledgeBase() {

    const container =
        document.getElementById(
            "knowledge-base-list"
        );

    try {

        const result =
            await API.knowledgeBase();

        const documents =
            result.data.documents || [];

        if (!documents.length) {

            container.innerHTML = `
                <div class="empty-state-small">
                    No documents found.
                </div>
            `;

            return;
        }

        container.innerHTML = "";

        documents.forEach(
            doc => {

                const button =
                    document.createElement(
                        "button"
                    );

                button.className =
                    "kb-button";

                button.innerHTML = `

                    <span class="kb-icon">
                        ◇
                    </span>

                    <span class="kb-name">
                        ${escapeHtml(
                            doc.name
                        )}
                    </span>

                `;

                button.addEventListener(
                    "click",
                    () => {

                        const query =
                            `What is the ${doc.name.toLowerCase()} policy?`;

                        sendMessage(query);
                    }
                );

                container.appendChild(
                    button
                );
            }
        );

    } catch (error) {

        console.error(
            "Failed to load knowledge base:",
            error
        );

        container.innerHTML = `
            <div class="error-small">
                Failed to load knowledge base.
            </div>
        `;
    }
}