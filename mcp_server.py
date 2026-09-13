from fastmcp import FastMCP

from agent.tools import check_job_application_status

mcp = FastMCP("Naukri Application Lookup")


@mcp.tool()
def lookup_job_application(record_id: str) -> dict:
    """Look up a Naukri job application by record ID.

    Returns the application's current status, expected salary,
    application age, priority-review flag, and escalation recommendation.
    Raises ValueError when the record ID does not exist.
    """
    return check_job_application_status(record_id)


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=8000,
    )