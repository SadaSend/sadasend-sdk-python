import unittest

from sadasend.errors import (
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


class TestErrors(unittest.TestCase):
    def test_hierarchy(self):
        self.assertTrue(issubclass(AuthenticationError, SadaSendError))
        self.assertTrue(issubclass(InsufficientScopeError, SadaSendError))
        self.assertTrue(issubclass(InvalidFromError, SadaSendError))
        self.assertTrue(issubclass(DomainNotFoundError, SadaSendError))
        self.assertTrue(issubclass(DomainNotVerifiedError, SadaSendError))
        self.assertTrue(issubclass(RecipientNotAllowlistedError, SadaSendError))
        self.assertTrue(issubclass(RecipientSuppressedError, SadaSendError))
        self.assertTrue(issubclass(IdempotencyKeyReusedError, SadaSendError))
        self.assertTrue(issubclass(IdempotencyInProgressError, SadaSendError))
        self.assertTrue(issubclass(RateLimitError, SadaSendError))
        self.assertTrue(issubclass(ServerError, SadaSendError))
        self.assertTrue(issubclass(ConnectionFailedError, SadaSendError))
        self.assertTrue(issubclass(SadaSendError, Exception))

    def test_domain_not_verified_error_records(self):
        records = [
            {"type": "TXT", "host": "@", "value": "v=spf1 ...", "verdict": "fail"},
            {"type": "CNAME", "host": "mail._domainkey", "value": "dkim.sadasend.com", "verdict": "pass"},
        ]
        err = DomainNotVerifiedError(
            code="domain_not_verified",
            status=403,
            message="Domain has not passed DNS verification.",
            body={"records": records},
        )
        self.assertEqual(err.records, records)
        self.assertEqual(err.code, "domain_not_verified")
        self.assertEqual(err.status, 403)
        self.assertEqual(str(err), "Domain has not passed DNS verification.")

        # Empty fallback
        empty_err = DomainNotVerifiedError("domain_not_verified", 403, "Msg", {})
        self.assertEqual(empty_err.records, [])

    def test_recipient_not_allowlisted_error(self):
        err = RecipientNotAllowlistedError(
            code="recipient_not_allowlisted",
            status=403,
            message="Recipient outside key allowlist.",
            body={"recipient": "external@stranger.com", "allowlist": ["@internal.corp"]},
        )
        self.assertEqual(err.recipient, "external@stranger.com")
        self.assertEqual(err.allowlist, ["@internal.corp"])

        empty_err = RecipientNotAllowlistedError("recipient_not_allowlisted", 403, "Msg", {})
        self.assertIsNone(empty_err.recipient)
        self.assertEqual(empty_err.allowlist, [])

    def test_recipient_suppressed_error(self):
        err = RecipientSuppressedError(
            code="recipient_suppressed",
            status=422,
            message="Address is on the suppression list.",
            body={"recipient": "user@domain.com", "reason": "unsubscribe"},
        )
        self.assertEqual(err.recipient, "user@domain.com")
        self.assertEqual(err.reason, "unsubscribe")

    def test_rate_limit_error(self):
        err = RateLimitError(
            code="rate_limit_exceeded",
            status=429,
            message="Rate limit exceeded.",
            body={"retryAfterSeconds": 15},
        )
        self.assertEqual(err.retry_after_seconds, 15.0)
        self.assertFalse(err.is_account_throttle)

        # Account throttle variant
        throttle_err = RateLimitError(
            code="account_throttled",
            status=429,
            message="Account throttled for deliverability reputation.",
            body={"retry_after_seconds": 3600},
        )
        self.assertEqual(throttle_err.retry_after_seconds, 3600.0)
        self.assertTrue(throttle_err.is_account_throttle)

        # Override parameter wins over body
        override_err = RateLimitError(
            code="rate_limit_exceeded",
            status=429,
            message="Limit",
            body={"retryAfterSeconds": 5},
            retry_after_seconds=30.0,
        )
        self.assertEqual(override_err.retry_after_seconds, 30.0)

    def test_connection_failed_error(self):
        cause = OSError("Network is unreachable")
        err = ConnectionFailedError("Could not reach API", cause=cause, attempts=3)
        self.assertEqual(err.code, "connection_failed")
        self.assertEqual(err.status, 0)
        self.assertIs(err.cause, cause)
        self.assertEqual(err.attempts, 3)

    def test_to_error_mappings(self):
        # 429 maps to RateLimitError
        e429 = to_error(429, {"error": "rate_limit_exceeded", "message": "Slow down"}, retry_after_seconds=10)
        self.assertIsInstance(e429, RateLimitError)
        self.assertEqual(e429.retry_after_seconds, 10)

        # 500+ maps to ServerError
        e500 = to_error(500, {"error": "internal_server_error", "message": "Internal error"})
        self.assertIsInstance(e500, ServerError)
        self.assertEqual(e500.status, 500)

        e503 = to_error(503, {"error": "service_unavailable", "message": "Temporarily down"})
        self.assertIsInstance(e503, ServerError)

        # 401 with standard or missing code
        e401_missing = to_error(401, {"error": "missing_api_key", "message": "No key"})
        self.assertIsInstance(e401_missing, AuthenticationError)

        e401_generic = to_error(401, {"message": "Invalid token"})
        self.assertIsInstance(e401_generic, AuthenticationError)

        # Specific guardrails
        self.assertIsInstance(
            to_error(403, {"error": "insufficient_scope", "message": "No send scope"}),
            InsufficientScopeError,
        )
        self.assertIsInstance(
            to_error(400, {"error": "invalid_from", "message": "Bad from"}),
            InvalidFromError,
        )
        self.assertIsInstance(
            to_error(404, {"error": "domain_not_found", "message": "Domain missing"}),
            DomainNotFoundError,
        )
        self.assertIsInstance(
            to_error(403, {"error": "domain_not_verified", "message": "Verify DNS"}),
            DomainNotVerifiedError,
        )
        self.assertIsInstance(
            to_error(403, {"error": "recipient_not_allowlisted", "message": "Refused"}),
            RecipientNotAllowlistedError,
        )
        self.assertIsInstance(
            to_error(422, {"error": "recipient_suppressed", "message": "Suppressed"}),
            RecipientSuppressedError,
        )
        self.assertIsInstance(
            to_error(409, {"error": "idempotency_key_reused", "message": "Reused"}),
            IdempotencyKeyReusedError,
        )
        self.assertIsInstance(
            to_error(409, {"error": "idempotency_key_in_progress", "message": "In progress"}),
            IdempotencyInProgressError,
        )

        # Unknown future error degrades to base SadaSendError without throwing
        unknown = to_error(400, {"error": "new_feature_guardrail", "message": "Future API message", "docs": "https://sadasend.com/docs"})
        self.assertIs(type(unknown), SadaSendError)
        self.assertEqual(unknown.code, "new_feature_guardrail")
        self.assertEqual(unknown.docs, "https://sadasend.com/docs")

    def test_is_retryable_classification(self):
        # Retryable: transient, server issues, connection failures, idempotency in progress
        self.assertTrue(is_retryable(ServerError("internal", 500, "Error")))
        self.assertTrue(is_retryable(RateLimitError("rate_limit", 429, "Limit")))
        self.assertTrue(is_retryable(IdempotencyInProgressError("idempotency_key_in_progress", 409, "Progress")))
        self.assertTrue(is_retryable(ConnectionFailedError("Failed", Exception(), 1)))

        # NEVER retryable: guardrail refusals and hard client errors
        self.assertFalse(is_retryable(AuthenticationError("missing_key", 401, "Auth")))
        self.assertFalse(is_retryable(InsufficientScopeError("scope", 403, "Scope")))
        self.assertFalse(is_retryable(RecipientNotAllowlistedError("allowlist", 403, "Not allowed")))
        self.assertFalse(is_retryable(RecipientSuppressedError("suppressed", 422, "Suppressed")))
        self.assertFalse(is_retryable(DomainNotVerifiedError("unverified", 403, "Unverified")))
        self.assertFalse(is_retryable(IdempotencyKeyReusedError("reused", 409, "Reused")))
        self.assertFalse(is_retryable(InvalidFromError("invalid_from", 400, "Invalid from")))
        self.assertFalse(is_retryable(DomainNotFoundError("domain_not_found", 404, "Not found")))


if __name__ == "__main__":
    unittest.main()
