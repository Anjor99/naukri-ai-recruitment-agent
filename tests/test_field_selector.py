from agent.field_selector import FieldSelector


def main() -> None:
    selector = FieldSelector()

    queries = [
        # Single field
        "what is the status of my application",
        "what is my expected salary",
        "how many days since we created this application",
        "is my application flagged",
        "should it be escalated",

        # Multiple fields
        "what is my status and expected salary",
        "tell me the status and how many days old my application is",
        "give me the status, expected salary and whether it is flagged",
        "tell me my status and whether my application should be escalated",

        # All details
        "give me all my application details",
        "tell me everything about my application",

        # Supported + unsupported
        "give me the status and applicant name",
        "tell me my expected salary and applicant email",
        "give me the status and phone number",

        # Unsupported
        "what is the applicant name",
        "what is the applicant email",
        "what is my phone number",
        "what job title did I apply for",
    ]

    for query in queries:
        result = selector.classify(query)

        print("\n" + "=" * 75)
        print(f"QUERY: {query}")

        print("\nSUPPORTED FIELDS:")

        if result.requested_fields:
            for match in result.requested_fields:
                print(
                    f"  {match.field.value:<30} "
                    f"{match.confidence:.4f} "
                    f"<- {match.clause}"
                )
        else:
            print("  NONE")

        print("\nUNSUPPORTED REQUESTS:")

        if result.unsupported_fields:
            for item in result.unsupported_fields:
                print(
                    f"  {item.clause:<40} "
                    f"{item.confidence:.4f}"
                )
        else:
            print("  NONE")

        print(
            f"\nDETAILS REQUESTED: "
            f"{result.details_requested}"
        )


if __name__ == "__main__":
    main()