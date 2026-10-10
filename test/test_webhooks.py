import hashlib
import hmac
import json
import time
import unittest

from sadasend.webhooks import (
    DEFAULT_TOLERANCE_SECONDS,
    EVENT_TYPES,
    SIGNATURE_HEADER,
    parse_webhook,
    verify_webhook,
)


def make_signature(secret: str, body: str, at: float) -> str:
    t = int(at)
    v1 = hmac.new(
        secret.encode("utf-8"),
        f"{t}.{body}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"t={t},v1={v1}"


class TestWebhooks(unittest.TestCase):
    SECRET = "whsec_live_test_secret_998877"
    BODY = '{"id":"evt_123","type":"email.delivered","data":{"messageId":"msg_001","recipient":"user@acme.com"}}'

    def test_constants(self):
        self.assertEqual(SIGNATURE_HEADER, "sadasend-signature")
        self.assertEqual(DEFAULT_TOLERANCE_SECONDS, 300)
        self.assertIn("email.sent", EVENT_TYPES)
        self.assertIn("email.delivered", EVENT_TYPES)
        self.assertIn("email.bounced", EVENT_TYPES)
        self.assertIn("email.complained", EVENT_TYPES)
        self.assertIn("email.refused", EVENT_TYPES)

    def test_valid_signature_str_body(self):
        now = time.time()
        header = make_signature(self.SECRET, self.BODY, now)
        self.assertTrue(verify_webhook(self.SECRET, self.BODY, header, at=now))

    def test_valid_signature_bytes_body(self):
        now = time.time()
        header = make_signature(self.SECRET, self.BODY, now)
        # Passing bytes directly as received in raw ASGI/WSGI requests
        self.assertTrue(verify_webhook(self.SECRET, self.BODY.encode("utf-8"), header, at=now))

    def test_wrong_secret_fails(self):
        now = time.time()
        header = make_signature(self.SECRET, self.BODY, now)
        self.assertFalse(verify_webhook("whsec_wrong_secret", self.BODY, header, at=now))

    def test_body_altered_fails(self):
        now = time.time()
        header = make_signature(self.SECRET, self.BODY, now)
        self.assertFalse(verify_webhook(self.SECRET, self.BODY + " ", header, at=now))

    def test_reserialized_body_fails(self):
        raw = '{\n  "id": "evt_123",\n  "type": "email.delivered"\n}'
        now = time.time()
        header = make_signature(self.SECRET, raw, now)
        reserialized = json.dumps(json.loads(raw))

        self.assertTrue(verify_webhook(self.SECRET, raw, header, at=now))
        # Re-serialized changes formatting and whitespace, so it must not verify
        self.assertFalse(verify_webhook(self.SECRET, reserialized, header, at=now))

    def test_invalid_headers(self):
        now = time.time()
        # None, empty, whitespace
        self.assertFalse(verify_webhook(self.SECRET, self.BODY, None, at=now))
        self.assertFalse(verify_webhook(self.SECRET, self.BODY, "", at=now))
        self.assertFalse(verify_webhook(self.SECRET, self.BODY, "   ", at=now))

        # Missing v1
        self.assertFalse(verify_webhook(self.SECRET, self.BODY, f"t={int(now)}", at=now))
        # Missing t
        self.assertFalse(verify_webhook(self.SECRET, self.BODY, "v1=abcd1234ef", at=now))
        # Malformed
        self.assertFalse(verify_webhook(self.SECRET, self.BODY, "garbage_header_no_equals", at=now))
        self.assertFalse(verify_webhook(self.SECRET, self.BODY, "t=invalid_timestamp,v1=abcd", at=now))

    def test_forged_timestamp_fails(self):
        old_time = time.time() - 100
        header = make_signature(self.SECRET, self.BODY, old_time)
        v1 = header.split("v1=")[1]

        # Attacker tries to reuse v1 with a newer timestamp
        forged_header = f"t={int(time.time())},v1={v1}"
        self.assertFalse(verify_webhook(self.SECRET, self.BODY, forged_header))

    def test_expired_timestamp_fails(self):
        now = time.time()
        expired_time = now - DEFAULT_TOLERANCE_SECONDS - 5
        header = make_signature(self.SECRET, self.BODY, expired_time)

        # Fails with current time
        self.assertFalse(verify_webhook(self.SECRET, self.BODY, header, at=now))
        # Passes if explicitly evaluated at the past time
        self.assertTrue(verify_webhook(self.SECRET, self.BODY, header, at=expired_time))

    def test_future_timestamp_within_tolerance(self):
        now = time.time()
        future_time = now + 30.0  # 30 seconds clock drift
        header = make_signature(self.SECRET, self.BODY, future_time)
        self.assertTrue(verify_webhook(self.SECRET, self.BODY, header, at=now))

    def test_custom_tolerance(self):
        now = time.time()
        drift_time = now - 20
        header = make_signature(self.SECRET, self.BODY, drift_time)

        # Fails with 10s tolerance
        self.assertFalse(verify_webhook(self.SECRET, self.BODY, header, at=now, tolerance_seconds=10))
        # Passes with 30s tolerance
        self.assertTrue(verify_webhook(self.SECRET, self.BODY, header, at=now, tolerance_seconds=30))

    def test_parse_webhook_success(self):
        now = time.time()
        header = make_signature(self.SECRET, self.BODY, now)

        # With str body
        event = parse_webhook(self.SECRET, self.BODY, header, at=now)
        self.assertIsInstance(event, dict)
        self.assertEqual(event["id"], "evt_123")
        self.assertEqual(event["type"], "email.delivered")
        self.assertEqual(event["data"]["recipient"], "user@acme.com")

        # With bytes body
        event_bytes = parse_webhook(self.SECRET, self.BODY.encode("utf-8"), header, at=now)
        self.assertIsInstance(event_bytes, dict)
        self.assertEqual(event_bytes["id"], "evt_123")

    def test_parse_webhook_invalid_returns_none(self):
        now = time.time()
        header = make_signature(self.SECRET, self.BODY, now)

        # Wrong secret returns None
        self.assertIsNone(parse_webhook("wrong_secret", self.BODY, header, at=now))

        # Non-JSON payload with valid HMAC returns None
        not_json = "plain text message not a json dict"
        valid_hdr_bad_json = make_signature(self.SECRET, not_json, now)
        self.assertIsNone(parse_webhook(self.SECRET, not_json, valid_hdr_bad_json, at=now))

        # JSON primitive (e.g. integer) returns None because event must be a dict
        number_json = "12345"
        valid_hdr_num = make_signature(self.SECRET, number_json, now)
        self.assertIsNone(parse_webhook(self.SECRET, number_json, valid_hdr_num, at=now))


if __name__ == "__main__":
    unittest.main()
