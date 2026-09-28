import unittest
from app.core import classify, validate_model_result


class TriageTests(unittest.TestCase):
    def test_refund_is_reviewed(self):
        decision = classify("Refund pending", "Please refund my order.")
        self.assertEqual(decision.category, "refund")
        self.assertTrue(decision.needs_human_review)
        self.assertNotIn("approved", decision.draft_reply.lower())

    def test_security_issue_escalates_even_if_llm_calls_it_normal(self):
        raw = {"category": "other", "priority": "normal", "sentiment": "neutral", "confidence": 0.99}
        decision = validate_model_result(raw, "Account hacked", "I see an unauthorized charge")
        self.assertEqual(decision.priority, "high")
        self.assertTrue(decision.needs_human_review)

    def test_malformed_llm_response_rejected(self):
        with self.assertRaises(ValueError):
            validate_model_result({"category": "refund", "priority": "low", "sentiment": "neutral", "confidence": 4}, "A", "B")

    def test_unknown_ticket_requires_review(self):
        decision = classify("Question", "I would like some information")
        self.assertEqual(decision.category, "other")
        self.assertTrue(decision.needs_human_review)


if __name__ == "__main__":
    unittest.main()
