# Support Ticket AI Triage

A human-in-the-loop ticket triage API. It detects topic, urgency and sentiment, drafts a reply, and requires human review for risky cases. The default rules engine is deterministic and works offline. Optionally, an OpenAI-compatible LLM produces structured output, which is schema-validated before it is accepted.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.api:app --reload
```

Open http://127.0.0.1:8000/docs and call `POST /triage`:

```json
{"ticket_id":"T-100", "subject":"Refund pending", "message":"My refund has not arrived after 12 business days. Order 12345."}
```

Optional LLM: set `OPENAI_API_KEY`; optionally set `OPENAI_MODEL` (default `gpt-4o-mini`) and `OPENAI_BASE_URL`. The service sends masked ticket text to the configured provider only when a key is set. Use fictional or approved data for demonstrations.

Set `REVIEW_TOKEN` to enable reviewer actions. `GET /reviews` and `POST /reviews/{ticket_id}` require the `X-Review-Token` header. The latter accepts `{"decision":"approved"}` or `{"decision":"rejected"}`. Without a configured token, reviewer endpoints remain disabled. The queue persists decisions in SQLite at `TRIAGE_DB_PATH` (default `data/triage.sqlite3`) without storing raw ticket text.

Container: `docker build -t ticket-triage . && docker run --rm -p 8000:8000 -e REVIEW_TOKEN=replace-me -v triage-data:/app/data ticket-triage`.

```bash
python -m unittest discover -s tests -v
python -m app.evaluate
```

## Design

`ticket -> rules / optional LLM -> validated category & priority -> safety gate -> draft for human review`

The LLM never makes a final refund or account decision. High-priority, payment-related and low-confidence tickets require human review. The service does not invent order status, refund approval, or delivery dates. Output includes `reason` and `model_used` to support audit and comparison. `app.evaluate` prints per-case accuracy on a small labeled, synthetic fixture; it is a smoke evaluation, not a production benchmark.

Email addresses and phone-like sequences are masked before an optional external LLM call. The original text is used only in process for local safety checks and is not stored in the decision queue. This regex masking is best-effort and does not replace a real privacy review.

## Limitations

English-only keyword rules are intentionally simple. The reviewer token is a demo control, not user management. Before production: label real cases, measure per-category precision/recall and escalation rates, review privacy and retention, add robust authentication and audit trails, multilingual evaluation, and rate limiting.

See [architecture and safety decisions](docs/architecture.md) for design trade-offs and references.
