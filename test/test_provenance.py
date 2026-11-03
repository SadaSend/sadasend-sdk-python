import sys
from pathlib import Path
_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import os
import unittest
from unittest.mock import patch

from sadasend import SadaSend
from test.test_client import make_mock_opener


class TestProvenance(unittest.TestCase):
    def test_client_level_defaults_from_constructor(self):
        opener, calls = make_mock_opener([
            (200, {"org": "Acme", "plan": "scale"}, {}),
        ])
        client = SadaSend(
            api_key="sada_live_sk_test",
            default_channel="sdk",
            default_source="backend",
            default_agent_name="billing-worker",
            opener=opener,
        )

        client.account.get()
        self.assertEqual(len(calls), 1)
        headers = calls[0]["headers"]
        self.assertEqual(headers["x-sadasend-channel"], "sdk")
        self.assertEqual(headers["x-sadasend-source"], "backend")
        self.assertEqual(headers["x-sadasend-agent"], "billing-worker")

    def test_client_level_defaults_from_env(self):
        opener, calls = make_mock_opener([
            (200, {"org": "Acme", "plan": "scale"}, {}),
        ])
        env = {
            "SADASEND_API_KEY": "sada_live_sk_test",
            "SADASEND_CHANNEL": "mcp",
            "SADASEND_SOURCE": "agent",
            "SADASEND_AGENT_NAME": "cursor-agent",
        }
        with patch.dict(os.environ, env):
            client = SadaSend(opener=opener)
            client.account.get()

        self.assertEqual(len(calls), 1)
        headers = calls[0]["headers"]
        self.assertEqual(headers["x-sadasend-channel"], "mcp")
        self.assertEqual(headers["x-sadasend-source"], "agent")
        self.assertEqual(headers["x-sadasend-agent"], "cursor-agent")

    def test_per_request_provenance_in_send(self):
        opener, calls = make_mock_opener([
            (202, {"id": "msg_agent_123", "status": "queued"}, {}),
        ])
        client = SadaSend("sada_live_sk_test", opener=opener)

        res = client.emails.send(
            from_="agent@acme.com",
            to="user@example.com",
            subject="Autonomous Action",
            text="Completed task",
            channel="mcp",
            source="agent",
            agent_name="claude-code",
        )

        self.assertEqual(res["id"], "msg_agent_123")
        self.assertEqual(len(calls), 1)
        req = calls[0]

        # 1. Provenance verified in request body
        body = req["body"]
        self.assertEqual(body["channel"], "mcp")
        self.assertEqual(body["source"], "agent")
        self.assertEqual(body["agent_name"], "claude-code")

        # 2. Provenance verified in request headers
        headers = req["headers"]
        self.assertEqual(headers["x-sadasend-channel"], "mcp")
        self.assertEqual(headers["x-sadasend-source"], "agent")
        self.assertEqual(headers["x-sadasend-agent"], "claude-code")

    def test_priority_header_stamping(self):
        opener, calls = make_mock_opener([
            (202, {"id": "msg_p0", "status": "queued"}, {}),
        ])
        client = SadaSend("sada_live_sk_test", opener=opener)

        res = client.emails.send(
            from_="auth@acme.com",
            to="user@example.com",
            subject="Security Alert",
            text="Verify your login",
            priority="auth",
        )
        self.assertEqual(res["id"], "msg_p0")
        self.assertEqual(calls[0]["headers"]["x-sadasend-priority"], "auth")
        self.assertEqual(calls[0]["body"]["priority"], "auth")

    def test_provenance_dictionary_support(self):
        opener, calls = make_mock_opener([
            (202, {"id": "msg_prov", "status": "queued"}, {}),
        ])
        client = SadaSend("sada_live_sk_test", opener=opener)

        res = client.emails.send(
            from_="bot@acme.com",
            to="user@example.com",
            subject="Weekly Sync",
            text="Automated sync",
            provenance={
                "channel": "sdk",
                "source": "automation",
                "agent_name": "sync-bot",
                "priority": "billing",
            },
        )
        self.assertEqual(res["id"], "msg_prov")
        self.assertEqual(len(calls), 1)
        req = calls[0]
        self.assertEqual(req["body"]["provenance"]["channel"], "sdk")
        self.assertEqual(req["headers"]["x-sadasend-channel"], "sdk")
        self.assertEqual(req["headers"]["x-sadasend-source"], "automation")
        self.assertEqual(req["headers"]["x-sadasend-agent"], "sync-bot")
        self.assertEqual(req["headers"]["x-sadasend-priority"], "billing")


if __name__ == "__main__":
    unittest.main()
