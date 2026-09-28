import os
import tempfile
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app import api
from app.storage import ReviewQueue


class ReviewAPITests(unittest.TestCase):
    def test_review_requires_token_and_duplicate_cannot_reset_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(api, "queue", ReviewQueue(f"{directory}/review.db")), patch.dict(os.environ, {"REVIEW_TOKEN": "test-only-token"}):
                client = TestClient(api.app)
                body = {"ticket_id": "T-42", "subject": "Refund pending", "message": "I need a refund for my order"}
                first = client.post("/triage", json=body)
                self.assertEqual(first.status_code, 200)
                self.assertEqual(first.json()["status"], "pending_review")
                self.assertEqual(client.get("/reviews").status_code, 403)
                headers = {"X-Review-Token": "test-only-token"}
                self.assertEqual(len(client.get("/reviews", headers=headers).json()["tickets"]), 1)
                reviewed = client.post("/reviews/T-42", json={"decision": "approved"}, headers=headers)
                self.assertEqual(reviewed.json()["status"], "approved")
                self.assertEqual(client.post("/triage", json=body).status_code, 409)
                self.assertEqual(api.queue.get("T-42")["status"], "approved")


if __name__ == "__main__":
    unittest.main()
