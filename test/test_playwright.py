"""Tests for sadasend.playwright drop-in test fixtures."""

import unittest
from unittest.mock import MagicMock, patch

from sadasend import SadaSend
from sadasend.playwright import EphemeralInboxFixture, _HAS_PYTEST


class TestPlaywrightFixtures(unittest.TestCase):
    def setUp(self):
        self.client = SadaSend(api_key="sada_live_sk_test_playwright_fixture", base_url="http://api.test")
        self.dummy_inbox = {
            "id": "inbox_py_123",
            "email": "py-agent@sada.email",
            "alias": "py-agent",
            "domain": "sada.email",
            "ttlSeconds": 300,
        }

    def test_fixture_initialization(self):
        fixture = EphemeralInboxFixture(self.client, self.dummy_inbox)
        self.assertEqual(fixture.id, "inbox_py_123")
        self.assertEqual(fixture.email, "py-agent@sada.email")
        self.assertEqual(fixture.alias, "py-agent")
        self.assertEqual(fixture.domain, "sada.email")

    def test_wait_for_otp_returns_existing_code(self):
        self.client.inboxes.otp = MagicMock(return_value={
            "ok": True,
            "inboxId": "inbox_py_123",
            "code": "481920",
            "pending": False,
        })
        fixture = EphemeralInboxFixture(self.client, self.dummy_inbox)
        otp = fixture.wait_for_otp(timeout_ms=500)
        self.assertEqual(otp, "481920")

    def test_wait_for_code_alias(self):
        self.client.inboxes.otp = MagicMock(return_value={
            "ok": True,
            "inboxId": "inbox_py_123",
            "otp": "771122",
            "pending": False,
        })
        fixture = EphemeralInboxFixture(self.client, self.dummy_inbox)
        code = fixture.wait_for_code(timeout_ms=500)
        self.assertEqual(code, "771122")
        # camelCase check
        self.assertEqual(fixture.waitForCode(timeout_ms=500), "771122")

    def test_wait_for_magic_link(self):
        self.client.inboxes.otp = MagicMock(return_value={
            "ok": True,
            "inboxId": "inbox_py_123",
            "magicLink": "https://app.example.com/login?token=xyz",
        })
        fixture = EphemeralInboxFixture(self.client, self.dummy_inbox)
        link = fixture.wait_for_magic_link(timeout_ms=500)
        self.assertEqual(link, "https://app.example.com/login?token=xyz")
        self.assertEqual(fixture.waitForMagicLink(timeout_ms=500), "https://app.example.com/login?token=xyz")

    def test_wait_for_message(self):
        self.client.inboxes.messages = MagicMock(return_value={
            "ok": True,
            "messages": [
                {
                    "id": "msg_py_1",
                    "from": "auth@service.com",
                    "subject": "Your code",
                    "otp": "112233",
                }
            ],
        })
        fixture = EphemeralInboxFixture(self.client, self.dummy_inbox)
        msg = fixture.wait_for_message(timeout_ms=500)
        self.assertEqual(msg["id"], "msg_py_1")
        self.assertEqual(msg["otp"], "112233")
        self.assertEqual(fixture.waitForMessage(timeout_ms=500)["id"], "msg_py_1")

    def test_get_messages(self):
        self.client.inboxes.messages = MagicMock(return_value={
            "ok": True,
            "messages": [{"id": "m1"}, {"id": "m2"}],
        })
        fixture = EphemeralInboxFixture(self.client, self.dummy_inbox)
        msgs = fixture.get_messages()
        self.assertEqual(len(msgs), 2)
        self.assertEqual(fixture.getMessages()[0]["id"], "m1")

    def test_wait_for_otp_timeout(self):
        self.client.inboxes.otp = MagicMock(return_value={"ok": True, "pending": True})
        self.client.testing.wait_for_code = MagicMock(return_value={"ok": False})
        fixture = EphemeralInboxFixture(self.client, self.dummy_inbox)
        with self.assertRaises(TimeoutError):
            fixture.wait_for_otp(timeout_ms=50)

    def test_teardown_cleans_up_created_inbox(self):
        if not _HAS_PYTEST:
            return  # Skip pytest fixture test if pytest not installed in this runner
        from sadasend.playwright import create_inbox

        deleted_ids = []
        self.client.inboxes.create = MagicMock(return_value={
            "ok": True,
            "inbox": {"id": "inbox_clean_me", "email": "clean@sada.email"},
        })
        self.client.inboxes.delete = MagicMock(side_effect=lambda id: deleted_ids.append(id))

        gen = create_inbox(self.client)
        factory = next(gen)
        inbox_fixture = factory(alias="clean")
        self.assertEqual(inbox_fixture.id, "inbox_clean_me")
        self.assertEqual(deleted_ids, [])

        # Teardown triggered by completing the generator
        try:
            next(gen)
        except StopIteration:
            pass

        self.assertEqual(deleted_ids, ["inbox_clean_me"])


if __name__ == "__main__":
    unittest.main()

