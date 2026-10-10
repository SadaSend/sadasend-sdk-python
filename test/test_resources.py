import sys
from pathlib import Path
_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import unittest
from sadasend import SadaSend
from test.test_client import make_mock_opener


class TestResources(unittest.TestCase):
    def setUp(self):
        self.api_key = "sada_live_sk_test123"

    # 1. Account
    def test_account_operations(self):
        opener, calls = make_mock_opener([
            (200, {"id": "acc_1", "plan": "growth"}, {}),
            (200, {"delivered": 1500, "window": "14d"}, {}),
            (200, {"days": [{"count": 100}]}, {}),
            (200, {"open": False}, {}),
            (200, {"items": []}, {}),
            (200, {"grants": []}, {}),
        ])
        client = SadaSend(api_key=self.api_key, opener=opener)

        # get
        res = client.account.get()
        self.assertEqual(res["plan"], "growth")
        self.assertEqual(calls[-1]["method"], "GET")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/account")

        # stats
        res = client.account.stats(window="14d", by_tag="prod")
        self.assertEqual(res["delivered"], 1500)
        self.assertEqual(calls[-1]["method"], "GET")
        self.assertIn("window=14d", calls[-1]["url"])
        self.assertIn("by_tag=prod", calls[-1]["url"])

        # volume
        res = client.account.volume(window="7d")
        self.assertEqual(len(res["days"]), 1)
        self.assertEqual(calls[-1]["method"], "GET")
        self.assertIn("window=7d", calls[-1]["url"])

        # circuit_breakers
        res = client.account.circuit_breakers()
        self.assertEqual(res["open"], False)
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/account/circuit-breakers")

        # checklist
        res = client.account.checklist()
        self.assertEqual(res["items"], [])
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/account/checklist")

        # staff_access
        res = client.account.staff_access(limit=5)
        self.assertEqual(res["grants"], [])
        self.assertIn("limit=5", calls[-1]["url"])

    # 2. Domains
    def test_domains_operations(self):
        opener, calls = make_mock_opener([
            (200, {"domains": [{"id": "dom_123", "domain": "example.com"}]}, {}),
            (200, {"records": [{"type": "TXT", "host": "sadasend._domainkey"}]}, {}),
            (200, {"status": "verified"}, {}),
        ])
        client = SadaSend(api_key=self.api_key, opener=opener)

        # list
        res = client.domains.list()
        self.assertEqual(len(res["domains"]), 1)
        self.assertEqual(calls[-1]["method"], "GET")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/domains")

        # records
        res = client.domains.records("dom_123")
        self.assertEqual(len(res["records"]), 1)
        self.assertEqual(calls[-1]["method"], "GET")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/domains/dom_123/records")

        # verify
        res = client.domains.verify("dom_123", idempotency_key="idem_verify_1")
        self.assertEqual(res["status"], "verified")
        self.assertEqual(calls[-1]["method"], "POST")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/domains/dom_123/verify")
        self.assertEqual(calls[-1]["headers"]["idempotency-key"], "idem_verify_1")

    # 3. Emails
    def test_emails_operations(self):
        opener, calls = make_mock_opener([
            (200, {"id": "msg_1", "status": "queued"}, {}),
            (200, {"total": 2, "results": [{"id": "msg_a"}, {"id": "msg_b"}]}, {}),
            (200, {"id": "msg_1", "status": "delivered"}, {}),
            (200, {"messages": [{"id": "msg_1"}]}, {}),
            (200, {"id": "msg_1", "status": "queued"}, {}),
            (200, {"id": "msg_1", "status": "cancelled"}, {}),
        ])
        client = SadaSend(api_key=self.api_key, opener=opener)

        # send
        res = client.emails.send(
            from_="noreply@example.com",
            to="user@example.com",
            subject="Test Email",
            html="<p>Hello</p>",
            tags=["welcome"],
            dry_run=True,
            idempotency_key="idem_send_1",
        )
        self.assertEqual(res["id"], "msg_1")
        self.assertEqual(calls[-1]["method"], "POST")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/emails")
        self.assertEqual(calls[-1]["body"]["from"], "noreply@example.com")
        self.assertEqual(calls[-1]["body"]["to"], "user@example.com")
        self.assertEqual(calls[-1]["body"]["dry_run"], True)
        self.assertEqual(calls[-1]["headers"]["idempotency-key"], "idem_send_1")

        # batch
        res = client.emails.batch(
            emails=[
                {"from": "a@example.com", "to": "b@example.com", "subject": "A"},
                {"from": "a@example.com", "to": "c@example.com", "subject": "B"},
            ],
            idempotency_key="idem_batch_1",
        )
        self.assertEqual(res["total"], 2)
        self.assertEqual(calls[-1]["method"], "POST")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/emails/batch")
        self.assertEqual(len(calls[-1]["body"]["emails"]), 2)

        # get
        res = client.emails.get("msg_1")
        self.assertEqual(res["status"], "delivered")
        self.assertEqual(calls[-1]["method"], "GET")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/emails/msg_1")

        # list
        res = client.emails.list(status="delivered", limit=10)
        self.assertEqual(len(res["messages"]), 1)
        self.assertEqual(calls[-1]["method"], "GET")
        self.assertIn("status=delivered", calls[-1]["url"])
        self.assertIn("limit=10", calls[-1]["url"])

        # resend
        res = client.emails.resend("msg_1")
        self.assertEqual(res["status"], "queued")
        self.assertEqual(calls[-1]["method"], "POST")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/emails/msg_1/resend")

        # cancel
        res = client.emails.cancel("msg_1")
        self.assertEqual(res["status"], "cancelled")
        self.assertEqual(calls[-1]["method"], "DELETE")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/emails/msg_1")

    # 4. Keys & Keys Approvals
    def test_keys_and_approvals(self):
        opener, calls = make_mock_opener([
            (200, {"keys": [{"id": "key_1", "name": "Prod Agent"}]}, {}),
            (200, {"approvals": [{"id": "appr_1", "status": "pending"}]}, {}),
        ])
        client = SadaSend(api_key=self.api_key, opener=opener)

        # keys.list
        res = client.keys.list()
        self.assertEqual(len(res["keys"]), 1)
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/keys")

        # keys_approvals.list
        res = client.keys_approvals.list()
        self.assertEqual(len(res["approvals"]), 1)
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/keys/approvals")

    # 5. Support Tickets
    def test_support_tickets_operations(self):
        opener, calls = make_mock_opener([
            (200, {"tickets": [{"id": "tkt_1", "subject": "Quota increase"}]}, {}),
            (200, {"id": "tkt_1", "status": "open", "messages": []}, {}),
        ])
        client = SadaSend(api_key=self.api_key, opener=opener)

        res = client.support_tickets.list()
        self.assertEqual(len(res["tickets"]), 1)
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/support/tickets")

        res = client.support_tickets.get("tkt_1")
        self.assertEqual(res["status"], "open")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/support/tickets/tkt_1")

    # 6. Suppressions
    def test_suppressions_operations(self):
        opener, calls = make_mock_opener([
            (200, {"suppressions": [{"address": "quiet@example.com", "reason": "manual"}]}, {}),
            (200, {"address": "blocked@example.com", "reason": "manual"}, {}),
        ])
        client = SadaSend(api_key=self.api_key, opener=opener)

        # list
        res = client.suppressions.list(limit=25, reason="manual", q="quiet")
        self.assertEqual(len(res["suppressions"]), 1)
        self.assertEqual(calls[-1]["method"], "GET")
        self.assertIn("limit=25", calls[-1]["url"])
        self.assertIn("reason=manual", calls[-1]["url"])
        self.assertIn("q=quiet", calls[-1]["url"])

        # add
        res = client.suppressions.add("blocked@example.com", reason="manual")
        self.assertEqual(res["address"], "blocked@example.com")
        self.assertEqual(calls[-1]["method"], "POST")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/suppressions")
        self.assertEqual(calls[-1]["body"]["address"], "blocked@example.com")
        self.assertEqual(calls[-1]["body"]["reason"], "manual")

    # 7. Team
    def test_team_operations(self):
        opener, calls = make_mock_opener([
            (200, {"members": [{"id": "usr_1", "email": "owner@example.com", "role": "owner"}]}, {}),
        ])
        client = SadaSend(api_key=self.api_key, opener=opener)

        res = client.team.get()
        self.assertEqual(len(res["members"]), 1)
        self.assertEqual(calls[-1]["method"], "GET")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/team")

    # 8. Templates
    def test_templates_operations(self):
        opener, calls = make_mock_opener([
            (200, {"templates": [{"id": "tpl_1", "name": "receipt"}]}, {}),
            (200, {"id": "tpl_1", "subject": "Your receipt", "html": "<h1>Receipt</h1>"}, {}),
            (200, {"html": "<h1>Receipt for Alice</h1>", "subject": "Receipt"}, {}),
            (200, {"id": "msg_test_1", "status": "queued"}, {}),
        ])
        client = SadaSend(api_key=self.api_key, opener=opener)

        # list
        res = client.templates.list()
        self.assertEqual(len(res["templates"]), 1)
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/templates")

        # get
        res = client.templates.get("tpl_1")
        self.assertEqual(res["id"], "tpl_1")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/templates/tpl_1")

        # render
        res = client.templates.render("tpl_1", variables={"name": "Alice"})
        self.assertEqual(calls[-1]["method"], "POST")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/templates/tpl_1/render")
        self.assertEqual(calls[-1]["body"]["variables"]["name"], "Alice")

        # test
        res = client.templates.test("tpl_1", to="alice@example.com", variables={"name": "Alice"})
        self.assertEqual(res["status"], "queued")
        self.assertEqual(calls[-1]["method"], "POST")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/templates/tpl_1/test")
        self.assertEqual(calls[-1]["body"]["to"], "alice@example.com")

    # 9. Tools
    def test_tools_operations(self):
        opener, calls = make_mock_opener([
            (200, {"tools": ["dns", "spf", "dkim", "dmarc"]}, {}),
            (200, {"check": "dns", "valid": True}, {}),
        ])
        client = SadaSend(api_key=self.api_key, opener=opener)

        # list
        res = client.tools.list()
        self.assertEqual(len(res["tools"]), 4)
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/tools")

        # check
        res = client.tools.check("dns", subject="sadasend.com", selector="s1")
        self.assertTrue(res["valid"])
        self.assertEqual(calls[-1]["method"], "POST")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/tools/dns")
        self.assertEqual(calls[-1]["body"]["subject"], "sadasend.com")
        self.assertEqual(calls[-1]["body"]["selector"], "s1")

    # 10. Webhooks
    def test_webhooks_operations(self):
        opener, calls = make_mock_opener([
            (200, {"webhooks": [{"id": "wh_1", "url": "https://example.com/webhook"}]}, {}),
            (200, {"deliveries": [{"id": "del_1", "status": 200}]}, {}),
        ])
        client = SadaSend(api_key=self.api_key, opener=opener)

        # list
        res = client.webhooks.list()
        self.assertEqual(len(res["webhooks"]), 1)
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/webhooks")

        # deliveries
        res = client.webhooks.deliveries("wh_1", limit=10, event="email.delivered")
        self.assertEqual(len(res["deliveries"]), 1)
        self.assertEqual(calls[-1]["method"], "GET")
        self.assertIn("limit=10", calls[-1]["url"])
        self.assertIn("event=email.delivered", calls[-1]["url"])
