"""An exception class per failure mode, and every one of them carries the fix.

The standard is the one the free tools hold themselves to: a message that says
what is wrong and nothing about what to do is a message that generates a support
ticket. ``DomainNotVerifiedError`` carries the DNS records that are missing,
because the person reading it is about to go and look them up.

**These are raised, where the TypeScript SDK returns them.** That is a
deliberate difference rather than an inconsistency. The principle in both is
that a refusal must not be silently ignorable — and the mechanics that achieve
it differ by language. TypeScript's compiler will not let you touch ``.id``
without narrowing the union first, so a result object is safe there. Python has
no such check: an unexamined return value is a program that carries on as though
the mail went out. Here, the exception is what cannot be ignored.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

__all__ = [
    "SadaSendError",
    "AuthenticationError",
    "InsufficientScopeError",
    "InvalidFromError",
    "DomainNotFoundError",
    "DomainNotVerifiedError",
    "RecipientNotAllowlistedError",
    "RecipientSuppressedError",
    "IdempotencyKeyReusedError",
    "IdempotencyInProgressError",
    "UndeliverableRecipientError",
    "InvalidSubjectError",
    "InvalidDateError",
    "BatchSizeExceededError",
    "PlanTierInsufficientError",
    "AnonymousLimitExceededError",
    "InvitationAlreadyPendingError",
    "InvalidPlanError",
    "RateLimitError",
    "ServerError",
    "ConnectionFailedError",
    "to_error",
    "is_retryable",
]


class SadaSendError(Exception):
    """Base class. A code this SDK has not heard of arrives as one of these.

    An SDK a version behind the API should degrade to *less specific*, never to
    *raises on parse*.
    """

    def __init__(self, code: str, status: int, message: str, body: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.message = message
        self.body: Dict[str, Any] = body or {}
        self.docs: Optional[str] = self.body.get("docs")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"{type(self).__name__}({self.code!r}, status={self.status}, message={self.message!r})"


class AuthenticationError(SadaSendError):
    """The key is not valid, or was revoked. Nothing to retry."""


class InsufficientScopeError(SadaSendError):
    """The key has scopes, and the one this call needs is not among them.

    Not fixable in code, deliberately: widening a key is a decision someone
    makes in the dashboard, on purpose.
    """


class InvalidFromError(SadaSendError):
    """The ``from`` address did not parse as an email address."""


class DomainNotFoundError(SadaSendError):
    """That domain is not a sending domain on this account."""


class DomainNotVerifiedError(SadaSendError):
    """The domain exists but has not passed DNS verification.

    The records are on the exception, so the fix is here rather than a page away.
    """

    @property
    def records(self) -> List[Dict[str, Any]]:
        value = self.body.get("records")
        return value if isinstance(value, list) else []


class RecipientNotAllowlistedError(SadaSendError):
    """The guardrail that makes an agent safe to hand a key to.

    The allowlist is attached because the interesting question is always "what
    *is* it allowed to mail, then".
    """

    @property
    def recipient(self) -> Optional[str]:
        return self.body.get("recipient")

    @property
    def allowlist(self) -> List[str]:
        value = self.body.get("allowlist")
        return value if isinstance(value, list) else []


class RecipientSuppressedError(SadaSendError):
    """The address is on the suppression list.

    ``reason`` carries a judgement the caller should not make on its own: an
    ``unsubscribe`` is a person's decision and a ``hard_bounce`` is an address
    that does not exist. Neither is "retry later", which is why this is not
    retryable.
    """

    @property
    def recipient(self) -> Optional[str]:
        return self.body.get("recipient")

    @property
    def reason(self) -> Optional[str]:
        return self.body.get("reason")


class UndeliverableRecipientError(SadaSendError):
    """Real-time deliverability guardrail refusal (`verify_before_send=True`).

    The recipient failed syntax, DNS MX lookup, or was identified as a disposable/dead address.
    No email credits or monthly quota are debited.
    """

    @property
    def recipient(self) -> Optional[str]:
        return self.body.get("recipient")

    @property
    def reason(self) -> Optional[str]:
        return self.body.get("reason")

    @property
    def suggestion(self) -> Optional[str]:
        return self.body.get("suggestion")


class InvalidSubjectError(SadaSendError):
    """The subject violates RFC 5322 line limits (> 998 characters) or contains forbidden control characters."""


class InvalidDateError(SadaSendError):
    """The scheduled_at date is invalid, in the past, or beyond the maximum 72-hour scheduling window."""


class BatchSizeExceededError(SadaSendError):
    """The batch request exceeded the maximum allowed items (100)."""


class PlanTierInsufficientError(SadaSendError):
    """The requested feature (e.g. batch size or rate limit) requires an upgraded plan tier."""


class AnonymousLimitExceededError(SadaSendError):
    """The unauthenticated guest rate limit for email verification (5/day) has been exceeded."""


class InvitationAlreadyPendingError(SadaSendError):
    """A pending team invitation already exists for this email address."""


class InvalidPlanError(SadaSendError):
    """The selected plan cannot be purchased via this checkout route."""


class IdempotencyKeyReusedError(SadaSendError):
    """The same key with a different body. The first request stands."""


class IdempotencyInProgressError(SadaSendError):
    """The first request with this key has not finished.

    Retrying returns *its* result rather than sending again, so this one **is**
    retryable — and the client does retry it, which is the whole point of
    sending the key.
    """


class RateLimitError(SadaSendError):
    """Rate limited — by this key's own limit, or by the account-wide throttle.

    ``retry_after_seconds`` comes from the ``Retry-After`` header the API
    already sends. The client waits exactly that long rather than guessing,
    because a guess that is too short is what turns a limit into an outage.
    """

    def __init__(
        self,
        code: str,
        status: int,
        message: str,
        body: Optional[Dict[str, Any]] = None,
        retry_after_seconds: Optional[float] = None,
    ) -> None:
        super().__init__(code, status, message, body)
        if retry_after_seconds is None and self.body:
            value = self.body.get("retryAfterSeconds")
            if value is None:
                value = self.body.get("retry_after_seconds") or self.body.get("retry_after")
            try:
                retry_after_seconds = float(value) if value is not None else None
            except (TypeError, ValueError):
                retry_after_seconds = None
        self.retry_after_seconds = retry_after_seconds

    @property
    def is_account_throttle(self) -> bool:
        """True when the account is throttled for reputation, not merely over a key limit."""
        return self.code == "account_throttled"


class ServerError(SadaSendError):
    """5xx, or a body that was not the error envelope. Retryable."""


class ConnectionFailedError(SadaSendError):
    """The request never got an answer — DNS, TLS, a dropped socket, a timeout.

    Not knowing whether the API saw the request is a genuinely different
    situation from being told no, so it is a distinct class rather than a 500.

    **Not** named ``ConnectionError``. Python already has a builtin of that
    name, for socket-level failures, and exporting a different class under it
    would leave anyone writing ``except ConnectionError`` catching whichever one
    their imports happened to bind last. The TypeScript SDK can call its
    equivalent ``ConnectionError`` because TypeScript has no such builtin.
    """

    def __init__(self, message: str, cause: BaseException, attempts: int) -> None:
        super().__init__("connection_failed", 0, message)
        self.cause = cause
        self.attempts = attempts


_BY_CODE = {
    "missing_api_key": AuthenticationError,
    "invalid_api_key": AuthenticationError,
    "unauthenticated": AuthenticationError,
    "insufficient_scope": InsufficientScopeError,
    "invalid_from": InvalidFromError,
    "domain_not_found": DomainNotFoundError,
    "domain_not_verified": DomainNotVerifiedError,
    "recipient_not_allowlisted": RecipientNotAllowlistedError,
    "recipient_suppressed": RecipientSuppressedError,
    "idempotency_key_reused": IdempotencyKeyReusedError,
    "idempotency_key_in_progress": IdempotencyInProgressError,
    "undeliverable_recipient": UndeliverableRecipientError,
    "invalid_subject": InvalidSubjectError,
    "invalid_date": InvalidDateError,
    "batch_size_exceeded": BatchSizeExceededError,
    "plan_tier_insufficient": PlanTierInsufficientError,
    "anonymous_limit_exceeded": AnonymousLimitExceededError,
    "invitation_already_pending": InvitationAlreadyPendingError,
    "invalid_plan": InvalidPlanError,
    "free_plan_no_checkout": InvalidPlanError,
}


def to_error(
    status: int,
    body: Dict[str, Any],
    retry_after_seconds: Optional[float] = None,
) -> SadaSendError:
    """Map an error response onto a class. Unknown codes keep the body intact."""
    code = body.get("error") if isinstance(body.get("error"), str) else f"http_{status}"
    message = body.get("message")
    if not isinstance(message, str):
        message = f"The API returned {status} with no error message."

    cls = _BY_CODE.get(code)
    if cls:
        return cls(code, status, message, body)
    if status == 429:
        return RateLimitError(code, status, message, body, retry_after_seconds)
    if status >= 500:
        return ServerError(code, status, message, body)
    if status == 401:
        return AuthenticationError(code, status, message, body)
    return SadaSendError(code, status, message, body)


def is_retryable(error: SadaSendError) -> bool:
    """What is worth trying again.

    Every guardrail refusal is absent by design: a client that retries past an
    allowlist eventually gets through, and one that retried
    ``recipient_suppressed`` would automate the single thing the suppression
    list exists to stop.
    """
    return isinstance(error, (ServerError, RateLimitError, IdempotencyInProgressError, ConnectionFailedError))
