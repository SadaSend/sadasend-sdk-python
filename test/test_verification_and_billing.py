"""Tests for verification, batch verification, billing, and typed guardrails in Python SDK."""

import sys
from pathlib import Path
_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import unittest
from sadasend import SadaSend
from sadasend.errors import (
    UndeliverableRecipientError,
    InvalidSubjectError,
    InvalidDateError,
    BatchSizeExceededError,
    PlanTierInsufficientError,
    AnonymousLimitExceededError,
    InvitationAlreadyPendingError,
    InvalidPlanError,
    to_error,
)
from test.test_client import make_mock_opener


class TestVerificationAndGuardrails(unittest.TestCase):
    def test_typed_guardrail_exceptions(self):
        err = to_error(422, {
            "error": "undeliverable_recipient",
            "message": "Recipient MX missing",
            "recipient": "dead@example.invalid",
            "reason": "mx_missing",
            "suggestion": "dead@gmail.com",
        })
        self.assertIsInstance(err, UndeliverableRecipientError)
        self.assertEqual(err.recipient, "dead@example.invalid")
        self.assertEqual(err.reason, "mx_missing")
        self.assertEqual(err.suggestion, "dead@gmail.com")

        self.assertIsInstance(to_error(400, {"error": "invalid_subject"}), InvalidSubjectError)
        self.assertIsInstance(to_error(400, {"error": "invalid_date"}), InvalidDateError)
        self.assertIsInstance(to_error(400, {"error": "batch_size_exceeded"}), BatchSizeExceededError)
        self.assertIsInstance(to_error(403, {"error": "plan_tier_insufficient"}), PlanTierInsufficientError)
        self.assertIsInstance(to_error(429, {"error": "anonymous_limit_exceeded"}), AnonymousLimitExceededError)
        self.assertIsInstance(to_error(409, {"error": "invitation_already_pending"}), InvitationAlreadyPendingError)
        self.assertIsInstance(to_error(400, {"error": "invalid_plan"}), InvalidPlanError)

    def test_emails_send_verify_before_send_and_marketing(self):
        opener, calls = make_mock_opener([
            (202, {"id": "msg_py_1", "status": "queued"}, {}),
        ])
        client = SadaSend(api_key="sada_live_1234567890abcdef12345678", opener=opener)

        res = client.emails.send(
            from_="sender@sadasend.com",
            to="user@example.com",
            subject="Verification Test",
            text="Hello with verification",
            verify_before_send=True,
            marketing=True,
        )
        self.assertEqual(res["id"], "msg_py_1")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["body"]["verify_before_send"], True)
        self.assertEqual(calls[0]["body"]["marketing"], True)

    def test_tools_verify_and_verify_batch(self):
        opener, calls = make_mock_opener([
            (200, {
                "email": "test@example.com",
                "status": "deliverable",
                "verdict": "pass",
                "score": 98,
            }, {}),
            (200, {
                "ok": True,
                "total": 2,
                "deliverable": 2,
            }, {}),
            (200, {
                "url": "https://sadasend.com?utm_source=newsletter",
            }, {}),
        ])
        client = SadaSend(api_key="sada_live_1234567890abcdef12345678", opener=opener)

        v_res = client.tools.verify(email="test@example.com")
        self.assertEqual(v_res["status"], "deliverable")
        self.assertEqual(v_res["score"], 98)

        vb_res = client.tools.verifyBatch(emails=["a@b.com", "c@d.com"])
        self.assertTrue(vb_res["ok"])
        self.assertEqual(vb_res["total"], 2)

        utm_res = client.tools.build_utm(url="https://sadasend.com", source="newsletter")
        self.assertIn("utm_source=newsletter", utm_res["url"])

    def test_billing_credits_checkout(self):
        opener, calls = make_mock_opener([
            (200, {
                "transactionId": "txn_123",
                "checkoutUrl": "https://buy.paddle.com/txn_123",
                "priceId": "pri_123",
            }, {}),
        ])
        client = SadaSend(api_key="sada_live_1234567890abcdef12345678", opener=opener)

        res = client.billing.credits_checkout(pack="25k", type="verify", return_url="https://app.sadasend.com/verify")
        self.assertEqual(res["transactionId"], "txn_123")
        self.assertEqual(calls[0]["method"], "POST")
        self.assertEqual(calls[0]["url"], "https://api.sadasend.com/billing/credits/checkout")
        self.assertEqual(calls[0]["body"]["pack"], "25k")
        self.assertEqual(calls[0]["body"]["type"], "verify")

    def test_keys_approvals_alias(self):
        opener, calls = make_mock_opener([
            (200, {"pending": [{"id": "appr_1", "status": "pending_approval"}]}, {}),
        ])
        client = SadaSend(api_key="sada_live_1234567890abcdef12345678", opener=opener)

        res = client.keys.approvals()
        self.assertEqual(len(res["pending"]), 1)
        self.assertEqual(calls[0]["method"], "GET")
        self.assertEqual(calls[0]["url"], "https://api.sadasend.com/keys/approvals")

    def test_support_alias(self):
        opener, calls = make_mock_opener([
            (200, {"tickets": [{"id": "tick_1", "subject": "Help"}]}, {}),
            (200, {"id": "tick_1", "subject": "Help", "messages": []}, {}),
        ])
        client = SadaSend(api_key="sada_live_1234567890abcdef12345678", opener=opener)

        tickets = client.support.tickets()
        self.assertEqual(len(tickets["tickets"]), 1)
        ticket = client.support.ticket("tick_1")
        self.assertEqual(ticket["id"], "tick_1")


if __name__ == "__main__":
    unittest.main()
