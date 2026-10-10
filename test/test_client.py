import io
import json
import os
import unittest
import urllib.error
import warnings
from typing import Any, Dict, List, Optional
from unittest.mock import patch

warnings.filterwarnings("ignore", category=ResourceWarning)

from sadasend import (
    DEFAULT_BASE_URL,
    ConnectionFailedError,
    DomainNotVerifiedError,
    IdempotencyInProgressError,
    RateLimitError,
    RecipientNotAllowlistedError,
    RecipientSuppressedError,
    RetryPolicy,
    SadaSend,
    ServerError,
    VERSION,
)


class MockResponse:
    def __init__(
        self,
        status: int,
        body: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.status = status
        self.code = status
        self._body = body
        self.headers = headers or {"content-type": "application/json"}

    def read(self) -> bytes:
        if self._body is None:
            return b""
        if isinstance(self._body, bytes):
            return self._body
        if isinstance(self._body, str):
            return self._body.encode("utf-8")
        return json.dumps(self._body).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def make_mock_opener(responses: List[Any]):
    calls: List[Dict[str, Any]] = []

    def opener(request: urllib.request.Request, timeout: float = 30.0):
        headers_dict = dict(request.headers)
        # Add lowercase normalized headers
        data = request.data
        parsed_body = json.loads(data.decode("utf-8")) if data else None
        calls.append({
            "url": request.full_url,
            "method": request.get_method(),
            "headers": {k.lower(): v for k, v in headers_dict.items()},
            "body": parsed_body,
            "raw_data": data,
            "timeout": timeout,
        })
        next_item = responses.pop(0) if responses else responses[-1]
        if isinstance(next_item, Exception):
            raise next_item
        status, body, headers = next_item
        if status >= 400:
            fp = io.BytesIO(
                body.encode("utf-8") if isinstance(body, str) else (
                    json.dumps(body).encode("utf-8") if body is not None else b""
                )
            )
            hdrs = headers or {"content-type": "application/json"}
            raise urllib.error.HTTPError(
                url=request.full_url,
                code=status,
                msg="HTTP Error",
                hdrs=hdrs,
                fp=fp,
            )
        return MockResponse(status, body, headers)

    return opener, calls


class TestClient(unittest.TestCase):
    def test_init_with_key_and_env(self):
        # Direct key
        client = SadaSend(api_key="sada_live_sk_direct123")
        self.assertEqual(client._api_key, "sada_live_sk_direct123")
        self.assertEqual(client._base_url, DEFAULT_BASE_URL)

        # From env
        with patch.dict(os.environ, {"SADASEND_API_KEY": "sada_live_sk_env456"}):
            client_env = SadaSend()
            self.assertEqual(client_env._api_key, "sada_live_sk_env456")

        # Missing key raises ValueError
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as ctx:
                SadaSend()
            self.assertIn("No API key", str(ctx.exception))

    def test_custom_base_url_and_env(self):
        # Strips trailing slash
        client = SadaSend("key", base_url="https://custom.api.sadasend.com///")
        self.assertEqual(client._base_url, "https://custom.api.sadasend.com")

        with patch.dict(os.environ, {"SADASEND_BASE_URL": "http://localhost:8080/"}):
            client_env = SadaSend("key")
            self.assertEqual(client_env._base_url, "http://localhost:8080")

    def test_successful_send_and_standard_headers(self):
        opener, calls = make_mock_opener([
            (202, {"id": "msg_001", "status": "queued", "to": "user@example.com"}, {}),
        ])
        client = SadaSend("sada_live_sk_test", opener=opener)

        res = client.emails.send(
            from_="noreply@onboarding.sadasend.com",
            to="user@example.com",
            subject="Hello",
            html="<p>Hello world</p>",
        )

        self.assertEqual(res["id"], "msg_001")
        self.assertEqual(res["status"], "queued")
        # _normalise turned "to" into a list
        self.assertEqual(res["to"], ["user@example.com"])

        self.assertEqual(len(calls), 1)
        req = calls[0]
        self.assertEqual(req["url"], f"{DEFAULT_BASE_URL}/emails")
        self.assertEqual(req["method"], "POST")
        self.assertEqual(req["headers"]["authorization"], "Bearer sada_live_sk_test")
        self.assertEqual(req["headers"]["user-agent"], f"sadasend-python/{VERSION}")
        self.assertEqual(req["headers"]["content-type"], "application/json")
        # Generated UUID idempotency-key
        self.assertTrue(len(req["headers"]["idempotency-key"]) > 10)

    def test_custom_idempotency_key(self):
        opener, calls = make_mock_opener([
            (202, {"id": "msg_idem", "status": "queued"}, {}),
        ])
        client = SadaSend("key", opener=opener)

        client.emails.send(
            from_="a@b.com",
            to="c@d.com",
            subject="Test",
            text="Test",
            idempotency_key="custom_order_12345",
        )

        self.assertEqual(calls[0]["headers"]["idempotency-key"], "custom_order_12345")

    def test_same_idempotency_key_preserved_across_retries(self):
        # 500 then 503 then 202
        opener, calls = make_mock_opener([
            (500, {"error": "internal_error", "message": "Failure 1"}, {}),
            (503, {"error": "service_unavailable", "message": "Failure 2"}, {}),
            (202, {"id": "msg_ok", "status": "queued"}, {}),
        ])
        retry = RetryPolicy(max_retries=3, base_delay_ms=1, max_delay_ms=5)
        client = SadaSend("key", opener=opener, retry=retry)

        res = client.emails.send(from_="a@b.com", to="c@d.com", subject="Retry", text="Hi")
        self.assertEqual(res["id"], "msg_ok")
        self.assertEqual(len(calls), 3)

        keys = [c["headers"]["idempotency-key"] for c in calls]
        self.assertEqual(len(set(keys)), 1, "The exact same idempotency key must ride all attempts")

    def test_query_params_encoding_and_filtering(self):
        opener, calls = make_mock_opener([
            (200, {"messages": [], "total": 0}, {}),
        ])
        client = SadaSend("key", opener=opener)

        client.emails.list(limit=50, status="delivered", q=None, tag="marketing")

        self.assertEqual(len(calls), 1)
        url = calls[0]["url"]
        self.assertIn("/emails?", url)
        self.assertIn("limit=50", url)
        self.assertIn("status=delivered", url)
        self.assertIn("tag=marketing", url)
        self.assertNotIn("q=", url)  # None was filtered out

    def test_non_json_error_handling(self):
        # Cloudflare / proxy returns HTML 502
        opener, _ = make_mock_opener([
            (502, "<html><body>502 Bad Gateway</body></html>", {"content-type": "text/html"}),
        ])
        retry = RetryPolicy(max_retries=0)
        client = SadaSend("key", opener=opener, retry=retry)

        with self.assertRaises(ServerError) as ctx:
            client.account.get()

        err = ctx.exception
        self.assertEqual(err.status, 502)
        self.assertIn("502 Bad Gateway", err.message)

    def test_guardrail_refusal_raises_typed_error_without_retrying(self):
        refusals = [
            (403, {"error": "recipient_not_allowlisted", "message": "Outside allowlist", "recipient": "ext@bad.com", "allowlist": ["@good.com"]}, RecipientNotAllowlistedError),
            (422, {"error": "recipient_suppressed", "message": "Suppressed", "recipient": "sup@bad.com", "reason": "unsubscribe"}, RecipientSuppressedError),
            (403, {"error": "domain_not_verified", "message": "Unverified DNS", "records": [{"type": "TXT"}]}, DomainNotVerifiedError),
        ]

        for status, body, err_cls in refusals:
            opener, calls = make_mock_opener([(status, body, {})])
            retry = RetryPolicy(max_retries=3, base_delay_ms=1)
            client = SadaSend("key", opener=opener, retry=retry)

            with self.assertRaises(err_cls):
                client.emails.send(from_="test@domain.com", to="target@example.com", subject="Test", text="Hello")

            self.assertEqual(len(calls), 1, f"Guardrail refusal {body['error']} must NEVER be retried")

    def test_retry_in_progress_idempotency_succeeds(self):
        # 409 idempotency_key_in_progress followed by 202
        opener, calls = make_mock_opener([
            (409, {"error": "idempotency_key_in_progress", "message": "Request currently processing"}, {}),
            (202, {"id": "msg_finished", "status": "queued"}, {}),
        ])
        retry = RetryPolicy(max_retries=2, base_delay_ms=1)
        client = SadaSend("key", opener=opener, retry=retry)

        res = client.emails.send(from_="a@b.com", to="c@d.com", subject="Test", text="Wait")
        self.assertEqual(res["id"], "msg_finished")
        self.assertEqual(len(calls), 2)

    def test_connection_failure_exhausts_retries_and_raises(self):
        cause = urllib.error.URLError("Connection refused")
        opener, calls = make_mock_opener([cause, cause, cause, cause])
        retry = RetryPolicy(max_retries=2, base_delay_ms=1)
        client = SadaSend("key", opener=opener, retry=retry)

        with self.assertRaises(ConnectionFailedError) as ctx:
            client.account.get()

        err = ctx.exception
        self.assertIs(err.cause, cause)
        self.assertEqual(err.attempts, 3)  # Initial attempt + 2 retries = 3 attempts
        self.assertEqual(len(calls), 3)

    def test_recovered_connection_fault_preserves_idempotency_key(self):
        cause = urllib.error.URLError("Temporary socket glitch")
        opener, calls = make_mock_opener([
            cause,
            (202, {"id": "msg_recovered", "status": "queued"}, {}),
        ])
        retry = RetryPolicy(max_retries=2, base_delay_ms=1)
        client = SadaSend("key", opener=opener, retry=retry)

        res = client.emails.send(from_="a@b.com", to="c@d.com", subject="Test", text="Retry")
        self.assertEqual(res["id"], "msg_recovered")
        self.assertEqual(len(calls), 2)
        self.assertEqual(
            calls[0]["headers"]["idempotency-key"],
            calls[1]["headers"]["idempotency-key"],
        )

    def test_normalise_single_and_array_recipients(self):
        # Single recipient on single email
        res1 = SadaSend._normalise if hasattr(SadaSend, "_normalise") else None
        from sadasend._client import _normalise
        out1 = _normalise({"id": "1", "to": "person@example.com"})
        self.assertEqual(out1["to"], ["person@example.com"])

        # Multiple recipients
        out2 = _normalise({"id": "2", "to": ["a@b.com", "c@d.com"]})
        self.assertEqual(out2["to"], ["a@b.com", "c@d.com"])

        # In messages listing
        out3 = _normalise({
            "messages": [
                {"id": "3", "to": "single@example.com"},
                {"id": "4", "to": ["m1@example.com", "m2@example.com"]},
            ]
        })
        self.assertEqual(out3["messages"][0]["to"], ["single@example.com"])
        self.assertEqual(out3["messages"][1]["to"], ["m1@example.com", "m2@example.com"])

        # Non-dict is preserved untouched
        self.assertEqual(_normalise(None), None)
        self.assertEqual(_normalise("string"), "string")


if __name__ == "__main__":
    unittest.main()
