from dataset import JOB_APPLICATIONS


def check_job_application_status(record_id: str) -> dict:
    record = next(
        (
            application
            for application in JOB_APPLICATIONS
            if application["record_id"].upper() == record_id.upper()
        ),
        None,
    )

    if record is None:
        return {
            "record_id": record_id.upper(),
            "found": False,
            "error": "No application found with this record ID.",
        }

    flag_component = (
        1.0
        if record["flagged_priority_review"]
        else 0.0
    )

    # Normalized recency over the valid 0–30 day range.
    # 1.0 = created today
    # 0.0 = created 30 days ago
    recency_score = (
        30 - record["days_since_created"]
    ) / 30

    escalation_score = round(
        0.5 * flag_component
        + 0.5 * (1.0 - recency_score),
        4,
    )

    return {
        "record_id": record["record_id"],
        "found": True,
        "status": record["status"],
        "expected_salary_inr": record["expected_salary_inr"],
        "days_since_created": record["days_since_created"],
        "flagged_priority_review": record["flagged_priority_review"],
        "recommend_escalation": escalation_score >= 0.88,
    }