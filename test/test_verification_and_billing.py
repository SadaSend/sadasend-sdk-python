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

    def test_convenience_nested_resource_aliases(self):
        opener, calls = make_mock_opener([
            (200, {"inbox": {"id": "inb_nested"}}, {}),
            (200, {"code": "777888"}, {}),
            (200, {"code": "111222"}, {}),
            (200, {"routes": []}, {}),
            (200, {"messages": []}, {}),
            (200, {"reports": []}, {}),
            (200, {"domain": "corp.com", "dkimAlignmentPct": 100}, {}),
            (200, {"cooldown": True}, {}),
            (200, {"registered": True}, {}),
        ])
        client = SadaSend(api_key="sada_live_1234567890abcdef12345678", opener=opener)

        # inboxes.create alias to inboxes.ephemeral
        inb = client.inboxes.create(alias="agent-alias")
        self.assertEqual(inb["inbox"]["id"], "inb_nested")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/inboxes/ephemeral")

        # testing.waitForCode alias
        wfc = client.testing.waitForCode(to="t@corp.com")
        self.assertEqual(wfc["code"], "777888")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/testing/wait-for-code")

        # testing.inboxes.code
        tc = client.testing.inboxes.code("t@corp.com")
        self.assertEqual(tc["code"], "111222")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/testing/inboxes/t@corp.com/code")

        # inbound.routes.list & inbound.messages.list
        rts = client.inbound.routes.list()
        self.assertEqual(rts["routes"], [])
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/inbound/routes")

        msgs = client.inbound.messages.list()
        self.assertEqual(msgs["messages"], [])
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/inbound/messages")

        # dmarc.reports.list & dmarc.summary
        reps = client.dmarc.reports.list()
        self.assertEqual(reps["reports"], [])
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/dmarc/reports")

        summ = client.dmarc.summary("corp.com")
        self.assertEqual(summ["domain"], "corp.com")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/dmarc/domains/corp.com/summary")

        # arbiter.cooldowns.set & arbiter.tickets.create
        cd = client.arbiter.cooldowns.set("rec@corp.com", cooldown_seconds=3600)
        self.assertTrue(cd["cooldown"])
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/arbiter/recipients/rec@corp.com/cooldown")

        tk = client.arbiter.tickets.create("rec@corp.com", ticket_id="TICK-99")
        self.assertTrue(tk["registered"])
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/arbiter/tickets")

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
