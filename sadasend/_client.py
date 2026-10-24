"""The transport, the retry policy and the guarantees they carry.

Hand-written, and that is the point of 12.6. A stock generated client gives you
``send_email(body)`` and an ``UnexpectedStatus`` exception; everything that makes
this SDK worth installing — ``Retry-After`` obeyed rather than guessed at,
idempotency on by default, no guardrail refusal ever retried — lives in the part
a generator cannot write.

**Standard library only.** ``urllib.request`` rather than ``requests`` or
``httpx``. Both are near-universal in Python and both would still be a
dependency chain the customer resolves, audits and eventually gets a CVE notice
about — and the TypeScript SDK's headline property is that it has none. The cost
is real and worth naming: no connection pooling. A transactional send is one
request, so it does not bite here; a caller sending thousands in a loop should
know they are paying for a TCP handshake each time.
"""

from __future__ import annotations

import json
import os
import random
import time
import urllib.error
import urllib.request
import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from ._generated import (
        Account,
        Domains,
        Emails,
        Keys,
        KeysApprovals,
        SupportTickets,
        Suppressions,
        Team,
        Templates,
        Tools,
        Webhooks as WebhooksResource,
    )

from ._generated import RESOURCES, SPEC_VERSION
from .errors import ConnectionFailedError, SadaSendError, is_retryable, to_error

__all__ = ["SadaSend", "RetryPolicy", "VERSION", "DEFAULT_BASE_URL"]

VERSION = "0.1.1"
DEFAULT_BASE_URL = "https://api.sadasend.com"


class RetryPolicy:
    """When to try again, and how long to wait.

    Two rules, and the second is the one nobody implements.

    **Exponential backoff with full jitter.** Fixed backoff synchronises every
    client that was refused in the same second, so they all return together and
    are refused together — the thundering herd that turns a brief limit into a
    long one. Full jitter, a uniform draw from ``[0, backoff]``, spreads them.

    **``Retry-After`` wins, always.** The API sends it; it is the server saying
    exactly when the window rolls over. A client that guesses shorter makes the
    limit worse, and one that guesses longer makes the customer wait for
    nothing. The header is not advice.
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay_ms: int = 500,
        max_delay_ms: int = 8_000,
        max_retry_after_ms: int = 60_000,
    ) -> None:
        self.max_retries = max_retries
        self.base_delay_ms = base_delay_ms
        self.max_delay_ms = max_delay_ms
        #: How long a ``Retry-After`` may ask us to block before the client
        #: gives up and raises instead. An account throttled for reputation can
        #: be told to come back in an hour, and blocking a request handler for
        #: an hour is worse than raising an error the caller can schedule around.
        self.max_retry_after_ms = max_retry_after_ms

    def delay_for(
        self,
        attempt: int,
        error: SadaSendError,
        rand: Optional[Any] = None,
    ) -> Optional[float]:
        """Seconds to wait before ``attempt`` (1-based), or ``None`` for "stop".

        Pure, so the policy can be tested without sleeping — a retry test that
        actually waits is one nobody runs often enough to trust.
        """
        if attempt > self.max_retries:
            return None

        retry_after = getattr(error, "retry_after_seconds", None)
        if retry_after is not None:
            if retry_after * 1000 > self.max_retry_after_ms:
                return None
            # Not jittered and not backed off. The server named a time.
            return float(retry_after)

        draw = rand if rand is not None else random.random
        backoff = min(self.base_delay_ms * (2 ** (attempt - 1)), self.max_delay_ms)
        return (draw() * backoff) / 1000.0


class Billing:
    """`client.billing` — Paddle credit pack checkouts."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def credits_checkout(
        self,
        pack: str,
        type: str = "verify",
        return_url: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        **extra: Any,
    ) -> Dict[str, Any]:
        """Initialize a Paddle checkout transaction for prepaid verification or sending credit packs."""
        body: Dict[str, Any] = dict(extra)
        body["pack"] = pack
        body["type"] = type
        if return_url is not None:
            body["returnUrl"] = return_url
        return self._client._request("POST", "/billing/credits/checkout", body=body, idempotency_key=idempotency_key)


class Support:
    """Convenience alias for support tickets matching TypeScript SDK."""

    def __init__(self, resource: Any) -> None:
        self._resource = resource

    def tickets(self, **kwargs: Any) -> Dict[str, Any]:
        return self._resource.list(**kwargs)

    def ticket(self, id_: str) -> Dict[str, Any]:
        return self._resource.get(id_)


class SadaSend:
    """The SadaSend client.

    >>> sadasend = SadaSend(os.environ["SADASEND_API_KEY"])
    >>> result = sadasend.emails.send(from_="noreply@…", to="dana@example.com", subject="Hi", html="<p>Hi</p>")
    >>> result["status"]
    'queued'

    ``status`` is ``'pending_approval'`` when the key is in approval mode — the
    message is real and waiting for a person, not lost. That is a success: the
    send was accepted.
    """

    account: Account
    domains: Domains
    emails: Emails
    keys: Keys
    keys_approvals: KeysApprovals
    support_tickets: SupportTickets
    support: Support
    suppressions: Suppressions
    team: Team
    templates: Templates
    tools: Tools
    billing: Billing
    webhooks: WebhooksResource

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        retry: Optional[RetryPolicy] = None,
        opener: Optional[Any] = None,
        default_channel: Optional[str] = None,
        default_source: Optional[str] = None,
        default_agent_name: Optional[str] = None,
    ) -> None:
        key = api_key or os.environ.get("SADASEND_API_KEY")
        if not key:
            raise ValueError(
                "No API key. Pass one to SadaSend(key) or set SADASEND_API_KEY. "
                "Keys are created in the dashboard under Keys and shown once."
            )
        self._api_key = key
        self._base_url = (base_url or os.environ.get("SADASEND_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        #: Per attempt, not for the whole call including retries.
        self._timeout = timeout
        self._retry = retry or RetryPolicy()
        self._opener = opener or urllib.request.urlopen
        self._default_channel = default_channel or os.environ.get("SADASEND_CHANNEL")
        self._default_source = default_source or os.environ.get("SADASEND_SOURCE")
        self._default_agent_name = default_agent_name or os.environ.get("SADASEND_AGENT_NAME")
        self.spec_version = SPEC_VERSION

        for attribute, resource_cls in RESOURCES.items():
            setattr(self, attribute, resource_cls(self))

        self.billing = Billing(self)
        self.support = Support(self.support_tickets)
        if hasattr(self, "keys"):
            setattr(self.keys, "approvals", lambda: self.keys_approvals.list())
        if hasattr(self, "tools"):
            setattr(self.tools, "build_utm", getattr(self.tools, "utm", None))
            setattr(self.tools, "verifyBatch", getattr(self.tools, "verify_batch", None))

    # ------------------------------------------------------------ transport

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        url = f"{self._base_url}{path}"
        if params:
            from urllib.parse import urlencode

            filtered = {k: v for k, v in params.items() if v is not None}
            if filtered:
                url = f"{url}?{urlencode(filtered)}"

        request_headers: Dict[str, str] = {
            "authorization": f"Bearer {self._api_key}",
            "user-agent": f"sadasend-python/{VERSION}",
        }
        if self._default_agent_name:
            request_headers["x-sadasend-agent"] = self._default_agent_name
        if self._default_source:
            request_headers["x-sadasend-source"] = self._default_source
        if self._default_channel:
            request_headers["x-sadasend-channel"] = self._default_channel

        if body is not None and isinstance(body, dict):
            if body.get("agent_name"):
                request_headers["x-sadasend-agent"] = str(body["agent_name"])
            if body.get("source"):
                request_headers["x-sadasend-source"] = str(body["source"])
            if body.get("channel"):
                request_headers["x-sadasend-channel"] = str(body["channel"])

        if headers:
            for k, v in headers.items():
                if v is not None:
                    request_headers[str(k).lower()] = str(v)

        payload: Optional[bytes] = None
        if body is not None:
            request_headers["content-type"] = "application/json"
            payload = json.dumps(body).encode("utf-8")

        # Generated when absent on a write, which is the point: without one, a
        # retry after a timeout is a second email to a real person — and a
        # timeout is exactly when a client retries. The *same* key rides every
        # attempt; a key regenerated per attempt is no key at all.
        if method in ("POST", "PATCH", "PUT"):
            request_headers["idempotency-key"] = idempotency_key or str(uuid.uuid4())

        attempt = 1
        while True:
            status, response_body, retry_after = self._attempt(method, url, request_headers, payload)

            if status is None:
                error: SadaSendError = ConnectionFailedError(
                    f"Could not reach {self._base_url} after {attempt} "
                    f"attempt{'' if attempt == 1 else 's'}.",
                    response_body,  # the underlying exception
                    attempt,
                )
            elif 200 <= status < 300:
                return _normalise(response_body)
            else:
                error = to_error(status, response_body, retry_after)

            if not is_retryable(error) or attempt > self._retry.max_retries:
                raise error

            wait = self._retry.delay_for(attempt, error)
            # ``None`` means the policy declined — a ``Retry-After`` longer than
            # we will block for. The error carries the header, so the caller can
            # schedule it rather than being made to wait.
            if wait is None:
                raise error
            time.sleep(wait)
            attempt += 1

    def _attempt(self, method: str, url: str, headers: Dict[str, str], payload: Optional[bytes]):
        """One HTTP attempt. Returns ``(status, body_or_exception, retry_after)``.

        ``status is None`` means no answer at all.
        """
        request = urllib.request.Request(url, data=payload, headers=headers, method=method)
        try:
            with self._opener(request, timeout=self._timeout) as response:
                return response.status, _parse(response.read()), _retry_after(response.headers)
        except urllib.error.HTTPError as e:
            # A 4xx or 5xx: an answer, and the body is the error envelope.
            try:
                raw_body = e.read()
            finally:
                e.close()
            return e.code, _parse(raw_body), _retry_after(e.headers)
        except Exception as e:  # noqa: BLE001 - urllib raises a wide family here
            return None, e, None


def _normalise(body: Any) -> Any:
    """``to`` is a union on the wire; it is a list here.

    The API returns a bare string for one recipient and an array for several.
    That shape is fixed — the dashboard is built against it — but a client that
    passed the wart on would make ``to[0]`` return ``"d"`` on a single-recipient
    message, which is the silent kind of wrong.

    Done in the hand-written layer rather than in the generated methods, which
    must stay inert delegations, and keyed on the shape of the response rather
    than the path it came from, so a new endpoint returning messages is covered
    without anyone remembering to add it.

    The TypeScript SDK does the same, and a parity harness comparing the two
    against a live server is what found this: it normalised there and not here,
    so the same call in two languages returned two different types.
    """
    if not isinstance(body, dict):
        return body
    if isinstance(body.get("to"), str):
        body["to"] = [body["to"]]
    if "verifyBeforeSend" in body and "verify_before_send" not in body:
        body["verify_before_send"] = body.pop("verifyBeforeSend")
    if "agentName" in body and "agent_name" not in body:
        body["agent_name"] = body.pop("agentName")
    for key in ("messages", "approvals", "emails", "results", "items"):
        rows = body.get(key)
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict):
                    if isinstance(row.get("to"), str):
                        row["to"] = [row["to"]]
                    if "verifyBeforeSend" in row and "verify_before_send" not in row:
                        row["verify_before_send"] = row.pop("verifyBeforeSend")
                    if "agentName" in row and "agent_name" not in row:
                        row["agent_name"] = row.pop("agentName")
    return body


def _parse(raw: Any) -> Dict[str, Any]:
    """A proxy's HTML error page is not JSON.

    Kept as a body rather than allowed to raise, so the error can say what
    actually arrived instead of "Expecting value: line 1 column 1".
    """
    if isinstance(raw, str):
        raw_bytes = raw.encode("utf-8")
    elif isinstance(raw, (bytes, bytearray)):
        raw_bytes = bytes(raw)
    else:
        raw_bytes = str(raw or "").encode("utf-8")

    try:
        value = json.loads(raw_bytes.decode("utf-8"))
    except Exception:  # noqa: BLE001
        text = raw_bytes.decode("utf-8", "replace")[:200]
        return {"error": "invalid_response", "message": text or "The API returned an empty body."}
    return value if isinstance(value, dict) else {"value": value}


def _retry_after(headers: Any) -> Optional[float]:
    if not headers:
        return None
    raw = None
    if hasattr(headers, "get"):
        raw = headers.get("retry-after") or headers.get("Retry-After")
    if not raw and hasattr(headers, "items"):
        for k, v in headers.items():
            if str(k).lower() == "retry-after":
                raw = v
                break
    if not raw:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        # The header may also be an HTTP-date. Rare from our API, valid per RFC 9110.
        from email.utils import parsedate_to_datetime

        try:
            at = parsedate_to_datetime(str(raw))
        except (TypeError, ValueError):
            return None
        return max(0.0, at.timestamp() - time.time())
