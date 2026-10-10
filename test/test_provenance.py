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


if __name__ == "__main__":
    unittest.main()
