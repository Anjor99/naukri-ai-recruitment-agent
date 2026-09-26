const API = {

    async request(
        url,
        options = {}
    ) {

        const response = await fetch(
            url,
            {
                ...options,
                headers: {
                    "Content-Type": "application/json",
                    ...(options.headers || {})
                }
            }
        );

        let data = null;

        try {
            data = await response.json();
        } catch {
            data = null;
        }

        if (!response.ok) {

            const message =
                data?.detail ||
                data?.message ||
                `Request failed (${response.status})`;

            throw new Error(message);
        }

        return {
            data,
            headers: response.headers
        };
    },


    async ask(query, conversationId = null) {

        const payload = {
            query
        };

        if (conversationId) {
            payload.conversation_id = conversationId;
        }

        return this.request(
            "/ask",
            {
                method: "POST",
                body: JSON.stringify(payload)
            }
        );
    },


    async health() {

        return this.request(
            "/health"
        );
    },


    async knowledgeBase() {

        return this.request(
            "/knowledge-base"
        );
    },


    async application(recordId) {

        return this.request(
            `/application/${encodeURIComponent(recordId)}`
        );
    },


    async graph() {

        return this.request(
            "/graph"
        );
    }

};