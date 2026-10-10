"""``sadasend`` — the SadaSend client for Python.

Transactional email with guardrails an agent cannot talk its way past.

**Zero runtime dependencies.** Standard library only: ``urllib.request`` for the
transport, ``hmac`` for the webhook verifier. This is the one package a customer
installs, and every dependency it carried would be one they resolve, audit and
eventually get a CVE notice about.

The operations in ``_generated.py`` come from the same OpenAPI spec the
TypeScript SDK is checked against, regenerated in CI so a route added in the
morning cannot land without appearing here. Everything that carries a guarantee
— retries, ``Retry-After``, idempotency, the error classes, the verifier — is
hand-written, because a generator cannot write "never retry a guardrail
refusal".
"""

from ._client import DEFAULT_BASE_URL, RetryPolicy, SadaSend, VERSION
from ._generated import SPEC_VERSION
from .errors import (
    AuthenticationError,
    ConnectionFailedError,
    DomainNotFoundError,
    DomainNotVerifiedError,
    IdempotencyInProgressError,
    IdempotencyKeyReusedError,
    InsufficientScopeError,
    InvalidFromError,
    RateLimitError,
    RecipientNotAllowlistedError,
    RecipientSuppressedError,
    SadaSendError,
    ServerError,
    is_retryable,
    to_error,
)
from .webhooks import (
    DEFAULT_TOLERANCE_SECONDS,
    EVENT_TYPES,
    SIGNATURE_HEADER,
    parse_webhook,
    verify_webhook,
)

__version__ = VERSION

__all__ = [
    "SadaSend", "RetryPolicy", "VERSION", "DEFAULT_BASE_URL", "SPEC_VERSION",
    "SadaSendError", "AuthenticationError", "InsufficientScopeError", "InvalidFromError",
    "DomainNotFoundError", "DomainNotVerifiedError", "RecipientNotAllowlistedError",
    "RecipientSuppressedError", "IdempotencyKeyReusedError", "IdempotencyInProgressError",
    "RateLimitError", "ServerError", "ConnectionFailedError", "is_retryable", "to_error",
    "verify_webhook", "parse_webhook", "SIGNATURE_HEADER", "DEFAULT_TOLERANCE_SECONDS", "EVENT_TYPES",
]
