"""``sadasend.playwright`` — Official Playwright & Pytest drop-in test fixtures for SadaSend.

Provides drop-in test fixtures for ephemeral agent inboxes, reactive zero-polling
2FA OTP streams (<150ms), magic link verification, and automatic test teardown.

Usage with pytest and pytest-playwright:

```python
def test_2fa_signup(page, ephemeral_inbox):
    page.goto("https://app.example.com/signup")
    page.fill("#email", ephemeral_inbox.email)
    page.click("#submit")

    # Zero-polling reactive stream (<150ms)
    otp = ephemeral_inbox.wait_for_otp()
    page.fill("#otp", otp)

    assert page.is_visible("#dashboard")
```
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
from typing import Any, Callable, Dict, Generator, List, Optional

from ._client import SadaSend


class EphemeralInboxFixture:
    """Represents an isolated, temporary test mailbox provisioned for a test."""

    def __init__(self, client: SadaSend, data: Dict[str, Any]) -> None:
        self.client = client
        self.raw = data
        self.id: str = str(data.get("id") or "")
        self.email: str = str(data.get("email") or "")
        self.alias: str = str(data.get("alias") or "")
        self.domain: str = str(data.get("domain") or "")

    def wait_for_otp(self, timeout_ms: int = 30_000) -> str:
        """Waits for an OTP verification code via reactive Server-Sent Events stream (<150ms).

        Falls back to testing endpoint polling if SSE is disconnected.
        """
        # 1. Check existing messages first
        try:
            res = self.client.inboxes.otp(id=self.id)
            if isinstance(res, dict) and not res.get("pending"):
                code = res.get("code") or res.get("otp")
                if code:
                    return str(code)
        except Exception:
            pass

        # 2. Stream real-time SSE events (<150ms push latency)
        timeout_seconds = max(0.5, timeout_ms / 1000.0)
        start_time = time.time()
        stream_url = self.client.inboxes.stream_url(self.id)

        try:
            req = urllib.request.Request(
                stream_url,
                headers={
                    "authorization": f"Bearer {self.client._api_key}",
                    "accept": "text/event-stream",
                    "user-agent": "sadasend-python-playwright",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                current_event = "message"
                data_lines: List[str] = []
                for raw_line in resp:
                    if time.time() - start_time > timeout_seconds:
                        break
                    line = raw_line.decode("utf-8", "replace").rstrip("\r\n")
                    if line.startswith(":"):
                        continue
                    if not line:
                        if data_lines:
                            raw_data = "\n".join(data_lines)
                            try:
                                parsed = json.loads(raw_data)
                            except Exception:
                                parsed = {}
                            if current_event == "otp" and isinstance(parsed, dict):
                                code = parsed.get("code") or parsed.get("otp")
                                if code:
                                    return str(code)
                            elif current_event == "message" and isinstance(parsed, dict):
                                code = parsed.get("otp") or parsed.get("code")
                                if code:
                                    return str(code)
                            current_event = "message"
                            data_lines = []
                        continue
                    if line.startswith("event:"):
                        current_event = line[6:].strip()
                    elif line.startswith("data:"):
                        data_lines.append(line[5:].lstrip(" "))
        except Exception:
            pass

        # 3. Fallback: call testing.wait_for_code with remaining time
        remaining_ms = max(500, int((timeout_seconds - (time.time() - start_time)) * 1000))
        try:
            fallback = self.client.testing.wait_for_code(to=self.email, timeout_ms=min(remaining_ms, 5_000))
            if isinstance(fallback, dict) and fallback.get("code"):
                return str(fallback["code"])
        except Exception:
            pass

        raise TimeoutError(f"Timed out waiting for OTP on inbox {self.email} ({self.id}) after {timeout_ms}ms")

    def wait_for_code(self, timeout_ms: int = 30_000) -> str:
        """Bidirectional alias of `wait_for_otp`."""
        return self.wait_for_otp(timeout_ms=timeout_ms)

    def wait_for_magic_link(self, timeout_ms: int = 30_000) -> str:
        """Waits for an authentication or verification magic link URL."""
        # 1. Check existing messages first
        try:
            res = self.client.inboxes.otp(id=self.id)
            if isinstance(res, dict) and res.get("magicLink"):
                return str(res["magicLink"])
        except Exception:
            pass

        timeout_seconds = max(0.5, timeout_ms / 1000.0)
        start_time = time.time()
        stream_url = self.client.inboxes.stream_url(self.id)

        try:
            req = urllib.request.Request(
                stream_url,
                headers={
                    "authorization": f"Bearer {self.client._api_key}",
                    "accept": "text/event-stream",
                    "user-agent": "sadasend-python-playwright",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                current_event = "message"
                data_lines: List[str] = []
                for raw_line in resp:
                    if time.time() - start_time > timeout_seconds:
                        break
                    line = raw_line.decode("utf-8", "replace").rstrip("\r\n")
                    if line.startswith(":"):
                        continue
                    if not line:
                        if data_lines:
                            raw_data = "\n".join(data_lines)
                            try:
                                parsed = json.loads(raw_data)
                            except Exception:
                                parsed = {}
                            if isinstance(parsed, dict) and parsed.get("magicLink"):
                                return str(parsed["magicLink"])
                            current_event = "message"
                            data_lines = []
                        continue
                    if line.startswith("event:"):
                        current_event = line[6:].strip()
                    elif line.startswith("data:"):
                        data_lines.append(line[5:].lstrip(" "))
        except Exception:
            pass

        # Fallback: check messages
        try:
            msgs_res = self.client.inboxes.messages(id=self.id)
            if isinstance(msgs_res, dict):
                msgs = msgs_res.get("messages") or []
                for m in msgs:
                    if isinstance(m, dict) and m.get("magicLink"):
                        return str(m["magicLink"])
        except Exception:
            pass

        raise TimeoutError(f"Timed out waiting for magic link on inbox {self.email} ({self.id}) after {timeout_ms}ms")

    def wait_for_message(self, timeout_ms: int = 30_000) -> Dict[str, Any]:
        """Waits for the next inbound message received by this inbox."""
        try:
            msgs_res = self.client.inboxes.messages(id=self.id)
            if isinstance(msgs_res, dict):
                msgs = msgs_res.get("messages") or []
                if msgs:
                    return msgs[0]
        except Exception:
            pass

        timeout_seconds = max(0.5, timeout_ms / 1000.0)
        start_time = time.time()
        stream_url = self.client.inboxes.stream_url(self.id)

        try:
            req = urllib.request.Request(
                stream_url,
                headers={
                    "authorization": f"Bearer {self.client._api_key}",
                    "accept": "text/event-stream",
                    "user-agent": "sadasend-python-playwright",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                current_event = "message"
                data_lines: List[str] = []
                for raw_line in resp:
                    if time.time() - start_time > timeout_seconds:
                        break
                    line = raw_line.decode("utf-8", "replace").rstrip("\r\n")
                    if line.startswith(":"):
                        continue
                    if not line:
                        if data_lines:
                            raw_data = "\n".join(data_lines)
                            try:
                                parsed = json.loads(raw_data)
                            except Exception:
                                parsed = {}
                            if current_event == "message" and isinstance(parsed, dict):
                                return parsed
                            current_event = "message"
                            data_lines = []
                        continue
                    if line.startswith("event:"):
                        current_event = line[6:].strip()
                    elif line.startswith("data:"):
                        data_lines.append(line[5:].lstrip(" "))
        except Exception:
            pass

        raise TimeoutError(f"Timed out waiting for message on inbox {self.email} ({self.id}) after {timeout_ms}ms")

    def get_messages(self) -> List[Dict[str, Any]]:
        """Lists all inbound messages received by this inbox so far."""
        try:
            res = self.client.inboxes.messages(id=self.id)
            if isinstance(res, dict):
                return list(res.get("messages") or [])
        except Exception:
            pass
        return []

    # camelCase convenience aliases
    waitForOtp = wait_for_otp
    waitForCode = wait_for_code
    waitForMagicLink = wait_for_magic_link
    waitForMessage = wait_for_message
    getMessages = get_messages


# ----------------------------------------------------------------------
# Pytest Fixtures (Auto-registered when running pytest)
# ----------------------------------------------------------------------

try:
    import pytest
    _HAS_PYTEST = True
except ImportError:
    _HAS_PYTEST = False

if _HAS_PYTEST:
    @pytest.fixture
    def sadasend_client() -> SadaSend:
        """Returns an authenticated SadaSend client from SADASEND_API_KEY environment."""
        api_key = os.environ.get("SADASEND_API_KEY") or os.environ.get("SADASEND_TEST_API_KEY") or "sada_test_sk_playwright"
        base_url = os.environ.get("SADASEND_BASE_URL")
        return SadaSend(api_key=api_key, base_url=base_url)

    @pytest.fixture
    def create_inbox(sadasend_client: SadaSend) -> Generator[Callable[..., EphemeralInboxFixture], None, None]:
        """Factory fixture to create isolated ephemeral inboxes with automatic teardown."""
        created_ids: List[str] = []

        def _factory(
            alias: Optional[str] = None,
            domain: Optional[str] = None,
            ttl_seconds: int = 300,
            description: Optional[str] = "Pytest ephemeral inbox",
            **kwargs: Any,
        ) -> EphemeralInboxFixture:
            payload: Dict[str, Any] = {"ttlSeconds": ttl_seconds}
            if alias:
                payload["alias"] = alias
            if domain:
                payload["domain"] = domain
            if description:
                payload["description"] = description
            payload.update(kwargs)

            res = sadasend_client.inboxes.create(**payload)
            inbox_data = res.get("inbox") or res
            inbox_id = str(inbox_data.get("id") or "")
            created_ids.append(inbox_id)
            return EphemeralInboxFixture(sadasend_client, inbox_data)

        yield _factory

        # Teardown: delete all created inboxes
        for i_id in created_ids:
            try:
                sadasend_client.inboxes.delete(id=i_id)
            except Exception:
                pass

    @pytest.fixture
    def ephemeral_inbox(create_inbox: Callable[..., EphemeralInboxFixture]) -> EphemeralInboxFixture:
        """Drop-in fixture providing an isolated ephemeral inbox automatically created and torn down."""
        return create_inbox()

    # camelCase aliases for JavaScript/TypeScript familiarity
    ephemeralInbox = ephemeral_inbox
    createInbox = create_inbox
    sadasendClient = sadasend_client

