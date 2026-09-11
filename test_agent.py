import unittest
from hiver_agent import run_agent

class AgentTests(unittest.TestCase):
    def test_routine_delivery_is_auto_handled(self):
        result = run_agent("Where is my order tracking?")
        self.assertEqual(result.intent, "delivery")
        self.assertFalse(result.escalated)

    def test_sensitive_billing_is_escalated(self):
        result = run_agent("I think my card was stolen and there is fraud")
        self.assertTrue(result.escalated)
        self.assertIn("human", result.escalation_reason)

    def test_unclear_message_is_escalated(self):
        result = run_agent("Hello")
        self.assertEqual(result.intent, "other")
        self.assertTrue(result.escalated)

if __name__ == "__main__":
    unittest.main()
