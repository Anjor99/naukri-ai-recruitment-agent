def _format_status_response(
    status_result: dict,
    requested_fields: list[str],
    unsupported_fields: list[str] | None = None,
) -> str:

    unsupported_fields = unsupported_fields or []

    if not status_result.get("found", True):
        record_id = status_result.get("record_id")

        return (
            f"I couldn't find an application with record ID "
            f"**{record_id}**.\n\n"
            "Please check the record ID and try again."
        )

    record_id = status_result["record_id"]

    lines = [
        f"Application **{record_id}**:"
    ]

    field_labels = {
        "status": "Current status",
        "expected_salary_inr": "Expected salary",
        "days_since_created": "Days since created",
        "flagged_priority_review": "Priority review",
        "escalation": "Escalation recommended",
    }

    for field in requested_fields:

        if field == "status":
            lines.append(
                f"Current status: **{status_result['status']}**"
            )

        elif field == "expected_salary_inr":
            lines.append(
                f"Expected salary: "
                f"**₹{status_result['expected_salary_inr']:,}**"
            )

        elif field == "days_since_created":
            lines.append(
                f"Application was created "
                f"**{status_result['days_since_created']} days ago**."
            )

        elif field == "flagged_priority_review":
            value = (
                "Yes"
                if status_result["flagged_priority_review"]
                else "No"
            )

            lines.append(
                f"Flagged for priority review: **{value}**"
            )

        elif field == "escalation":
            value = (
                "Yes"
                if status_result["recommend_escalation"]
                else "No"
            )

            lines.append(
                f"Escalation recommended: **{value}**"
            )

    if unsupported_fields:
        lines.append("")

        for unsupported in unsupported_fields:
            lines.append(
                f"I don't have information for "
                f"**{unsupported}** in the application data."
            )

    return "\n".join(lines)