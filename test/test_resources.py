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
            (200, {"url": "https://sadasend.com?utm_source=agent"}, {}),
            (200, {"email": "test@example.com", "status": "deliverable"}, {}),
            (200, {"ok": True, "total": 2, "deliverable": 2}, {}),
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

        # utm
        utm_res = client.tools.utm(url="https://sadasend.com", source="agent", medium="email")
        self.assertIn("utm_source=agent", utm_res["url"])
        self.assertEqual(calls[-1]["method"], "POST")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/tools/utm")
        self.assertEqual(calls[-1]["body"]["url"], "https://sadasend.com")
        self.assertEqual(calls[-1]["body"]["source"], "agent")
        self.assertEqual(calls[-1]["body"]["medium"], "email")

        # verify
        v_res = client.tools.verify(email="test@example.com")
        self.assertEqual(v_res["status"], "deliverable")
        self.assertEqual(calls[-1]["method"], "POST")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/tools/verify")
        self.assertEqual(calls[-1]["body"]["email"], "test@example.com")

        # verify_batch
        vb_res = client.tools.verify_batch(emails=["a@b.com", "c@d.com"])
        self.assertTrue(vb_res["ok"])
        self.assertEqual(calls[-1]["method"], "POST")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/tools/verify/batch")
        self.assertEqual(calls[-1]["body"]["emails"], ["a@b.com", "c@d.com"])

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

    # 11. Inbound
    def test_inbound_operations(self):
        opener, calls = make_mock_opener([
            (200, {"routes": [{"id": "rt_1", "pattern": "*@inbound.example.com"}]}, {}),
            (200, {"route": {"id": "rt_1", "pattern": "*@inbound.example.com"}}, {}),
            (200, {"id": "rt_2", "pattern": "sales@*"}, {}),
            (200, {"id": "rt_1", "active": False}, {}),
            (200, {"deleted": True}, {}),
            (200, {"messages": [{"id": "in_msg_1", "from": "sender@external.com"}]}, {}),
            (200, {"id": "in_msg_1", "subject": "Contract"}, {}),
            (200, {"content": {"cleanMarkdown": "Hello", "hasQuotedHistory": False}, "security": {"injectionRiskScore": 0.05}}, {}),
            (200, {"matched": True, "targetUrl": "https://example.com/webhook"}, {}),
        ])
        client = SadaSend(api_key=self.api_key, opener=opener)

        # inbound_routes list & get
        routes = client.inbound_routes.list()
        self.assertEqual(len(routes["routes"]), 1)
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/inbound/routes")

        rt = client.inbound_routes.get("rt_1")
        self.assertEqual(rt["route"]["id"], "rt_1")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/inbound/routes/rt_1")

        # inbound_routes create
        created_rt = client.inbound_routes.create(pattern="sales@*", target_type="webhook", webhook_url="https://app.com/inbound", priority=10, active=True)
        self.assertEqual(created_rt["id"], "rt_2")
        self.assertEqual(calls[-1]["method"], "POST")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/inbound/routes")
        self.assertEqual(calls[-1]["body"]["pattern"], "sales@*")
        self.assertEqual(calls[-1]["body"]["targetType"], "webhook")

        # inbound_routes update
        updated_rt = client.inbound_routes.update("rt_1", pattern="vip@*", active=False)
        self.assertEqual(calls[-1]["method"], "PATCH")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/inbound/routes/rt_1")
        self.assertEqual(calls[-1]["body"]["pattern"], "vip@*")
        self.assertFalse(calls[-1]["body"]["active"])

        # inbound_routes delete
        del_rt = client.inbound_routes.delete("rt_1")
        self.assertTrue(del_rt["deleted"])
        self.assertEqual(calls[-1]["method"], "DELETE")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/inbound/routes/rt_1")

        # inbound_messages list & get
        msgs = client.inbound_messages.list(limit=5)
        self.assertEqual(len(msgs["messages"]), 1)
        self.assertIn("limit=5", calls[-1]["url"])

        single_msg = client.inbound_messages.get("in_msg_1")
        self.assertEqual(single_msg["id"], "in_msg_1")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/inbound/messages/in_msg_1")

        # inbound parse
        parsed = client.inbound.parse(subject="Update", text="Hello\n\n> Quoted text")
        self.assertEqual(parsed["content"]["cleanMarkdown"], "Hello")
        self.assertEqual(calls[-1]["method"], "POST")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/inbound/parse")

        # inbound simulate
        sim = client.inbound.simulate(recipient="test@inbound.example.com")
        self.assertTrue(sim["matched"])
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/inbound/simulate")

    # 12. DMARC
    def test_dmarc_operations(self):
        opener, calls = make_mock_opener([
            (200, {"reports": [{"id": "dm_rep_1", "org": "google.com"}]}, {}),
            (200, {"id": "dm_rep_1", "evaluated": True}, {}),
            (200, {"id": "dm_rep_2", "status": "processed"}, {}),
            (200, {"domain": "example.com", "dkimAlignmentPct": 100, "currentPolicy": "reject"}, {}),
            (200, {"threats": [{"ip": "1.2.3.4", "count": 42}]}, {}),
        ])
        client = SadaSend(api_key=self.api_key, opener=opener)

        # dmarc_reports list & get & create
        reps = client.dmarc_reports.list(limit=10)
        self.assertEqual(len(reps["reports"]), 1)
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/dmarc/reports?limit=10")

        rep = client.dmarc_reports.get("dm_rep_1")
        self.assertEqual(rep["id"], "dm_rep_1")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/dmarc/reports/dm_rep_1")

        created_rep = client.dmarc_reports.create(xml="<feedback>test</feedback>", filename="google.xml")
        self.assertEqual(created_rep["id"], "dm_rep_2")
        self.assertEqual(calls[-1]["method"], "POST")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/dmarc/reports")
        self.assertEqual(calls[-1]["body"]["xml"], "<feedback>test</feedback>")
        self.assertEqual(calls[-1]["body"]["filename"], "google.xml")

        # dmarc_domains summary
        summary = client.dmarc_domains.summary("example.com")
        self.assertEqual(summary["dkimAlignmentPct"], 100)
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/dmarc/domains/example.com/summary")

        # dmarc threats
        threats = client.dmarc.threats()
        self.assertEqual(len(threats["threats"]), 1)
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/dmarc/threats")

    # 13. Arbiter
    def test_arbiter_operations(self):
        opener, calls = make_mock_opener([
            (200, {"activeCooldowns": 3, "pendingHolds": 0}, {}),
            (200, {"cooldown": True, "expiresAt": "2026-10-31T00:00:00Z"}, {}),
            (200, {"cleared": True}, {}),
            (200, {"allowed": True}, {}),
            (200, {"registered": True, "ticketId": "TICK-101"}, {}),
            (200, {"deleted": True}, {}),
        ])
        client = SadaSend(api_key=self.api_key, opener=opener)

        # arbiter stats
        stats = client.arbiter.stats()
        self.assertEqual(stats["activeCooldowns"], 3)
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/arbiter/stats")

        # arbiter set cooldown
        set_res = client.arbiter_recipients.set_cooldown("lead@corp.com", cooldown_seconds=86400, priority="follow_up", agent_name="sales-bot")
        self.assertTrue(set_res["cooldown"])
        self.assertEqual(calls[-1]["method"], "POST")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/arbiter/recipients/lead@corp.com/cooldown")
        self.assertEqual(calls[-1]["body"]["cooldownSeconds"], 86400)
        self.assertEqual(calls[-1]["body"]["priority"], "follow_up")
        self.assertEqual(calls[-1]["body"]["agentName"], "sales-bot")

        # arbiter clear cooldown
        clr_res = client.arbiter_recipients.clear_cooldown("lead@corp.com")
        self.assertTrue(clr_res["cleared"])
        self.assertEqual(calls[-1]["method"], "DELETE")

        # arbiter recipient status
        st_res = client.arbiter_recipients.status("lead@corp.com")
        self.assertTrue(st_res["allowed"])
        self.assertEqual(calls[-1]["method"], "GET")

        # arbiter tickets create & delete
        t_create = client.arbiter_tickets.create(recipient="lead@corp.com", ticket_id="TICK-101", subject="Billing issue", hold_priority_threshold=3)
        self.assertTrue(t_create["registered"])
        self.assertEqual(calls[-1]["method"], "POST")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/arbiter/tickets")
        self.assertEqual(calls[-1]["body"]["recipient"], "lead@corp.com")
        self.assertEqual(calls[-1]["body"]["ticketId"], "TICK-101")
        self.assertEqual(calls[-1]["body"]["holdPriorityThreshold"], 3)

        t_del = client.arbiter_tickets.delete("lead@corp.com")
        self.assertTrue(t_del["deleted"])
        self.assertEqual(calls[-1]["method"], "DELETE")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/arbiter/tickets/lead@corp.com")

    # 14. Inboxes
    def test_inboxes_operations(self):
        opener, calls = make_mock_opener([
            (200, {"inboxes": [{"id": "inb_1"}]}, {}),
            (200, {"inbox": {"id": "inb_1", "email": "agent-1@test.sadasend.com"}}, {}),
            (200, {"inbox": {"id": "inb_1"}}, {}),
            (200, {"code": "849201", "magicLink": None}, {}),
            (200, {"messages": [{"id": "m1", "subject": "Your code"}]}, {}),
            (200, {"ingested": True, "otp": "999888"}, {}),
            (200, {"stream": "active"}, {}),
            (200, {"deleted": True}, {}),
        ])
        client = SadaSend(api_key=self.api_key, opener=opener)

        # inboxes list
        inb_list = client.inboxes.list()
        self.assertEqual(len(inb_list["inboxes"]), 1)
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/inboxes")

        # ephemeral inbox creation
        inb = client.inboxes.ephemeral(ttl_seconds=600, alias="pw-agent")
        self.assertEqual(inb["inbox"]["id"], "inb_1")
        self.assertEqual(calls[-1]["method"], "POST")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/inboxes/ephemeral")
        self.assertEqual(calls[-1]["body"]["ttlSeconds"], 600)
        self.assertEqual(calls[-1]["body"]["alias"], "pw-agent")

        # get inbox
        inb_info = client.inboxes.get("inb_1")
        self.assertEqual(inb_info["inbox"]["id"], "inb_1")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/inboxes/inb_1")

        # otp retrieval
        otp = client.inboxes.otp("inb_1")
        self.assertEqual(otp["code"], "849201")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/inboxes/inb_1/otp")

        # inbox messages
        msgs = client.inboxes.messages("inb_1")
        self.assertEqual(len(msgs["messages"]), 1)
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/inboxes/inb_1/messages")

        # inbox inbound ingestion
        inb_res = client.inboxes.inbound(to="inb_1@auth.sadasend.com", from_="auth@corp.com", subject="Verification", text="Your OTP is 999888")
        self.assertTrue(inb_res["ingested"])
        self.assertEqual(calls[-1]["method"], "POST")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/inboxes/inbound")
        self.assertEqual(calls[-1]["body"]["to"], "inb_1@auth.sadasend.com")

        # inboxes stream
        stream_res = client.inboxes.stream("inb_1")
        self.assertEqual(stream_res["stream"], "active")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/inboxes/inb_1/stream")

        # inboxes delete
        del_inb = client.inboxes.delete("inb_1")
        self.assertTrue(del_inb["deleted"])
        self.assertEqual(calls[-1]["method"], "DELETE")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/inboxes/inb_1")

    # 15. Testing
    def test_testing_operations(self):
        opener, calls = make_mock_opener([
            (200, {"status": "ingested", "id": "tst_msg_1"}, {}),
            (200, {"code": "123456"}, {}),
            (200, {"code": "654321"}, {}),
            (200, {"message": {"id": "m1", "subject": "Test"}}, {}),
        ])
        client = SadaSend(api_key=self.api_key, opener=opener)

        # testing inbound
        ing = client.testing.inbound(to="t@test.com", from_="f@test.com", subject="Test", text="Hello")
        self.assertEqual(ing["status"], "ingested")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/testing/inbound")

        # wait for code
        wfc = client.testing.wait_for_code(to="t@test.com", timeout_ms=5000)
        self.assertEqual(wfc["code"], "123456")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/testing/wait-for-code")

        # testing inboxes code & latest
        c = client.testing_inboxes.code("t@test.com")
        self.assertEqual(c["code"], "654321")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/testing/inboxes/t@test.com/code")

        latest = client.testing_inboxes.latest("t@test.com")
        self.assertEqual(latest["message"]["id"], "m1")
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/testing/inboxes/t@test.com/latest")

    # 16. Integrations
    def test_integrations_operations(self):
        opener, calls = make_mock_opener([
            (200, {"connected": True, "channel": "#alerts"}, {}),
        ])
        client = SadaSend(api_key=self.api_key, opener=opener)

        res = client.integrations.slack()
        self.assertTrue(res["connected"])
        self.assertEqual(calls[-1]["url"], "https://api.sadasend.com/integrations/slack")
