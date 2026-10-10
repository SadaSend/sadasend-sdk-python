"""The webhook signature verifier — written, not generated.

The plan is explicit that this one is hand-written: a signature check is not
something to leave to a generator. It is also the one piece of our security
every customer otherwise reimplements, and the one most likely to be got subtly
wrong — the usual mistakes are comparing with ``==``, forgetting the timestamp
is inside the signed material, and verifying the parsed object instead of the
raw body.

``hmac`` and ``hashlib`` are standard library, so this adds nothing to install.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional, Union

__all__ = [
    "SIGNATURE_HEADER", "DEFAULT_TOLERANCE_SECONDS", "EVENT_TYPES",
    "verify_webhook", "parse_webhook",
]

#: Every event an endpoint can subscribe to, and only those. Open and click
#: tracking is not shipped, and ``POST /webhooks`` refuses both by name — a list
#: offering an event the API rejects sends someone to write a handler for
#: something they cannot receive.
EVENT_TYPES = (
    "email.sent", "email.delivered", "email.bounced",
    "email.complained", "email.refused",
)

#: The header the API sends: ``t=<unix-seconds>,v1=<hex>``.
SIGNATURE_HEADER = "sadasend-signature"

#: Matching the server. Without a timestamp in the signed material a captured
#: request is a permanent credential; with one, it expires.
DEFAULT_TOLERANCE_SECONDS = 5 * 60


def verify_webhook(
    secret: str,
    body: Union[str, bytes],
    header: Optional[str],
    at: Optional[float] = None,
    tolerance_seconds: int = DEFAULT_TOLERANCE_SECONDS,
) -> bool:
    """Verify a webhook.

    ``body`` must be the **raw request body as it arrived**, byte for byte.
    Both ``str`` and ``bytes`` are accepted.
    ``json.dumps(request.json)`` is not the same string — key order and
    whitespace survive the wire and do not survive a round trip — and every
    signature will fail in a way that looks exactly like a wrong secret.

    .. code-block:: python

        raw = request.get_data()  # or request.body in Django/FastAPI
        if not verify_webhook(secret, raw, request.headers.get("sadasend-signature")):
            return "bad signature", 400
    """
    if not secret or body is None or not header:
        return False

    now = time.time() if at is None else at

    parts: Dict[str, str] = {}
    for part in header.split(","):
        name, sep, value = part.partition("=")
        if sep:
            parts[name.strip()] = value.strip()

    given = parts.get("v1")
    try:
        t = float(parts["t"])
    except (KeyError, TypeError, ValueError):
        return False
    if not given:
        return False

    # Checked before the HMAC, so an expired signature costs no crypto at all.
    if tolerance_seconds > 0 and abs(now - t) > tolerance_seconds:
        return False

    if isinstance(body, bytes):
        body_bytes = body
    elif isinstance(body, str):
        body_bytes = body.encode("utf-8")
    else:
        return False

    payload = f"{int(t)}.".encode("utf-8") + body_bytes
    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    # ``compare_digest``, not ``==``. A byte-by-byte early exit leaks how much of
    # a forged signature was correct, which is enough to build a valid one a byte
    # at a time.
    return hmac.compare_digest(expected, given)


def parse_webhook(
    secret: str,
    body: Union[str, bytes],
    header: Optional[str],
    at: Optional[float] = None,
    tolerance_seconds: int = DEFAULT_TOLERANCE_SECONDS,
) -> Optional[Dict[str, Any]]:
    """Verify and parse in one call, returning the event or ``None``.

    The shape most handlers want, and it makes the dangerous mistake harder:
    the raw body goes in, and there is no version of this that takes a dict.
    """
    if not verify_webhook(secret, body, header, at, tolerance_seconds):
        return None
    try:
        event = json.loads(body)
    except (ValueError, TypeError):
        return None
    return event if isinstance(event, dict) else None
