import tempfile
import sqlite3
import unittest
from pathlib import Path
from app.core import classify
from app.privacy import redact_pii
from app.storage import ReviewQueue


class WorkflowTests(unittest.TestCase):
    def test_pii_masked_before_external_model(self):
        masked = redact_pii("Contact tinh@example.com or +84 912 345 678")
        self.assertNotIn("tinh@example.com", masked)
        self.assertNotIn("912 345 678", masked)
        self.assertIn("[EMAIL]", masked)

    def test_queue_requires_review_and_persists_decision_without_message(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "triage.db")
            queue = ReviewQueue(path)
            result = queue.save("T-1", classify("Refund", "Please refund my order").dict())
            self.assertEqual(result["status"], "pending_review")
            self.assertEqual(len(ReviewQueue(path).list_pending()), 1)
            self.assertTrue(queue.review("T-1", "approved"))
            self.assertEqual(queue.get("T-1")["status"], "approved")
            self.assertFalse(queue.review("T-1", "rejected"))
            with self.assertRaises(sqlite3.IntegrityError):
                queue.save("T-1", classify("Delivery", "Please check shipping").dict())
            self.assertEqual(queue.get("T-1")["status"], "approved")
            self.assertNotIn("Please refund", Path(path).read_bytes().decode("utf-8", errors="ignore"))


if __name__ == "__main__":
    unittest.main()
