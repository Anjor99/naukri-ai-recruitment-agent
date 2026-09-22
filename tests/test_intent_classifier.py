from agent.intent_classifier import IntentClassifier


classifier = IntentClassifier()

queries = [
    "what is the status of APP-0001",
    "what is the application details",
    "what is the applicant name",
    "should it be escalated",
    "what is the escalation of my application",
    "how many days since we created this application",
    "how many days since created this application",
    "what is the interview process",
    "what is the notice period policy",
    "what is applicant data retention",
    "how does background verification work",
    "what is the weather in Mumbai",
]

for query in queries:
    result = classifier.classify(
        query,
        remembered_record_id="APP-0001",
    )

    print(f"\nQUERY: {query}")
    print(f"INTENT: {result.intent.value}")
    print(f"STATUS: {result.status_similarity:.4f}")
    print(f"RAG:    {result.rag_similarity:.4f}")
    print(f"MARGIN: {result.margin:.4f}")
    print(f"CONF:   {result.confidence:.4f}")