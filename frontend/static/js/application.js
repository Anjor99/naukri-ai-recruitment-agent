async function loadApplication(recordId) {

    const container =
        document.getElementById(
            "application-result"
        );

    if (!recordId) {
        return;
    }

    container.innerHTML = `
        <div class="loading-small">
            Loading application...
        </div>
    `;

    try {

        const result =
            await API.application(
                recordId
            );

        const application =
            result.data;

        container.innerHTML = `
            <div class="application-card">

                <div class="application-id">
                    ${escapeHtml(
                        application.record_id
                    )}
                </div>

                <div class="application-field">
                    <span>Status</span>
                    <strong>
                        ${escapeHtml(
                            application.status
                        )}
                    </strong>
                </div>

                <div class="application-field">
                    <span>Expected salary</span>
                    <strong>
                        ₹${Number(
                            application.expected_salary_inr
                        ).toLocaleString("en-IN")}
                    </strong>
                </div>

                <div class="application-field">
                    <span>Age</span>
                    <strong>
                        ${application.days_since_created} days
                    </strong>
                </div>

                <div class="application-field">
                    <span>Priority review</span>
                    <strong>
                        ${
                            application.flagged_priority_review
                                ? "Yes"
                                : "No"
                        }
                    </strong>
                </div>

                <div class="application-field">
                    <span>Escalation score</span>
                    <strong>
                        ${application.escalation_score}
                    </strong>
                </div>

                <div
                    class="
                        escalation-badge
                        ${
                            application.recommend_escalation
                                ? "escalation-yes"
                                : "escalation-no"
                        }
                    "
                >
                    ${
                        application.recommend_escalation
                            ? "Escalation recommended"
                            : "No escalation"
                    }
                </div>

            </div>
        `;

    } catch (error) {

        container.innerHTML = `
            <div class="application-error">
                ${escapeHtml(
                    error.message
                )}
            </div>
        `;
    }
}


function searchApplication() {

    const input =
        document.getElementById(
            "application-id-input"
        );

    const recordId =
        input.value.trim();

    if (!recordId) {
        return;
    }

    loadApplication(
        recordId
    );
}