def _format_status_response(
    status_result: dict,
    requested_fields: list[str],
) -> str:
    """Format only the application fields requested by the user."""

    record_id = status_result.get("record_id")

    if not record_id:
        return (
            "I couldn't find any application matching that record ID. "
            "Could you double-check the ID and try again?"
        )

    lines = []

    if "status" in requested_fields:
        status = status_result.get("status")
        lines.append(f"Current status: **{status}**")

    if "expected_salary_inr" in requested_fields:
        salary = status_result.get("expected_salary_inr")
        if salary is not None:
            lines.append(f"Expected salary: **₹{salary:,}**")

    if "days_since_created" in requested_fields:
        days = status_result.get("days_since_created")
        if days is not None:
            lines.append(f"Application was created **{days} days ago**.")

    if "flagged_priority_review" in requested_fields:
        flagged = status_result.get("flagged_priority_review")
        if flagged is not None:
            answer = "Yes" if flagged else "No"
            lines.append(
                f"Flagged for priority review: **{answer}**"
            )

    if "recommend_escalation" in requested_fields:
        recommend = status_result.get("recommend_escalation")

        if recommend:
            lines.append(
                "Escalation is **recommended** for this application."
            )
        else:
            lines.append(
                "Escalation is **not currently recommended** for this application."
            )

    return f"Application **{record_id}**:\n" + "\n".join(lines)