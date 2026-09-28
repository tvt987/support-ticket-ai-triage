# Architecture and safety decisions

## Request path

1. Receive and validate a ticket. Do not store the original message.
2. Without a model key, classify through an inspectable rules baseline. With a key, redact email and phone-like values before requesting structured JSON.
3. Validate model output against allowed categories, priorities and confidence bounds. On failure, fall back to local rules.
4. Apply local safety rules **after** the model result, so an urgent security or payment phrase escalates regardless of model classification.
5. Persist the decision and review status in SQLite. A reviewer token gates listing and approval/rejection. Duplicate ticket IDs cannot reset a reviewed case.

Review approval only changes the queue status; it does not send a message, issue a refund, or alter an account. That separation keeps this demo reversible.

## Evaluation and limitations

`python -m app.evaluate` measures category accuracy on five synthetic fixtures. Additional tests exercise PII masking, unsafe model output, escalation, persistence, authorization, and state transitions. Production use needs a real labeled dataset, per-class precision/recall, reviewer agreement, privacy controls and audit logging.

## Design references

- [LangGraph human-in-the-loop](https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/interrupts.mdx) for durable pause/resume semantics. This demo implements a smaller SQLite state machine, not LangGraph.
- [Presidio](https://github.com/data-privacy-stack/presidio) for the separate detection/anonymization concern. Regex masking here is narrower than Presidio and only a demonstration.
- [Langfuse](https://github.com/langfuse/langfuse) for the idea of tracing decisions and evaluations; full observability is a future improvement.

All code in this repository is independently written for this demo.
