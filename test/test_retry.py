import email.utils
import time
import unittest

from sadasend._client import RetryPolicy, _retry_after
from sadasend.errors import RateLimitError, ServerError


class TestRetry(unittest.TestCase):
    def test_default_retry_policy_values(self):
        policy = RetryPolicy()
        self.assertEqual(policy.max_retries, 3)
        self.assertEqual(policy.base_delay_ms, 500)
        self.assertEqual(policy.max_delay_ms, 8000)
        self.assertEqual(policy.max_retry_after_ms, 60000)

    def test_exponential_backoff_with_mock_rand(self):
        policy = RetryPolicy(max_retries=3, base_delay_ms=500, max_delay_ms=8000)
        err = ServerError("internal_error", 500, "Internal Server Error")

        # Mock random draw = 1.0 (maximum possible backoff for each attempt)
        # Attempt 1: 500 * 2^0 = 500ms = 0.5s
        delay1 = policy.delay_for(1, err, rand=lambda: 1.0)
        self.assertAlmostEqual(delay1, 0.5)

        # Attempt 2: 500 * 2^1 = 1000ms = 1.0s
        delay2 = policy.delay_for(2, err, rand=lambda: 1.0)
        self.assertAlmostEqual(delay2, 1.0)

        # Attempt 3: 500 * 2^2 = 2000ms = 2.0s
        delay3 = policy.delay_for(3, err, rand=lambda: 1.0)
        self.assertAlmostEqual(delay3, 2.0)

        # Attempt 4 (> max_retries): returns None (stop retrying)
        delay4 = policy.delay_for(4, err, rand=lambda: 1.0)
        self.assertIsNone(delay4)

    def test_full_jitter_distribution_boundaries(self):
        policy = RetryPolicy(max_retries=3, base_delay_ms=500, max_delay_ms=8000)
        err = ServerError("internal_error", 500, "Server Error")

        # Lower bound (draw = 0.0) is always 0.0s
        min_delay = policy.delay_for(2, err, rand=lambda: 0.0)
        self.assertEqual(min_delay, 0.0)

        # Half-way (draw = 0.5)
        half_delay = policy.delay_for(2, err, rand=lambda: 0.5)
        self.assertAlmostEqual(half_delay, 0.5)

    def test_max_delay_capping(self):
        # Base delay 5000, max delay 8000
        policy = RetryPolicy(max_retries=5, base_delay_ms=5000, max_delay_ms=8000)
        err = ServerError("internal_error", 500, "Server Error")

        # Attempt 1: 5000ms
        self.assertAlmostEqual(policy.delay_for(1, err, rand=lambda: 1.0), 5.0)

        # Attempt 2: 5000 * 2 = 10000ms -> capped at 8000ms = 8.0s
        self.assertAlmostEqual(policy.delay_for(2, err, rand=lambda: 1.0), 8.0)

        # Attempt 3: capped at 8.0s
        self.assertAlmostEqual(policy.delay_for(3, err, rand=lambda: 1.0), 8.0)

    def test_retry_after_exact_value_without_jitter_or_escalation(self):
        policy = RetryPolicy(max_retries=3, max_retry_after_ms=60000)
        err = RateLimitError("rate_limit_exceeded", 429, "Too many requests", retry_after_seconds=7.0)

        # Obeyed directly: attempt 1 and attempt 2 both return exactly 7.0s
        self.assertEqual(policy.delay_for(1, err), 7.0)
        self.assertEqual(policy.delay_for(2, err), 7.0)

    def test_excessive_retry_after_declined(self):
        # max_retry_after_ms is 60_000 (60s). Server asks for 1 hour (3600s).
        policy = RetryPolicy(max_retries=3, max_retry_after_ms=60000)
        throttled = RateLimitError(
            "account_throttled",
            429,
            "Account throttled for deliverability reputation",
            retry_after_seconds=3600.0,
        )

        # The policy declines to block the caller for an hour, returning None
        self.assertIsNone(policy.delay_for(1, throttled))

    def test_retry_after_header_parser(self):
        # Numeric seconds
        self.assertEqual(_retry_after({"retry-after": "12"}), 12.0)
        self.assertEqual(_retry_after({"Retry-After": "4.5"}), 4.5)

        # Missing or empty
        self.assertIsNone(_retry_after(None))
        self.assertIsNone(_retry_after({}))
        self.assertIsNone(_retry_after({"retry-after": ""}))

        # RFC 9110 HTTP-date
        now = time.time()
        future_str = email.utils.formatdate(now + 15, usegmt=True)
        parsed = _retry_after({"retry-after": future_str})
        self.assertIsNotNone(parsed)
        # Should be roughly 15 seconds
        self.assertTrue(13.0 <= parsed <= 16.0)

        # Invalid date string
        self.assertIsNone(_retry_after({"retry-after": "invalid-date-not-a-number"}))


if __name__ == "__main__":
    unittest.main()
