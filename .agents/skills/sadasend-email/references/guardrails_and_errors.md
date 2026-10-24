# SadaSend Guardrails & Error Reference for AI Agents

SadaSend is engineered to prevent autonomous AI agents from hallucinating recipients, leaking confidential data, or destroying sending domain reputation. This reference details each guardrail error in Python, what triggers it, and how an agent can self-correct.

---

## 1. Recipient Allowlist Guardrail (`RecipientNotAllowlistedError`)

- **HTTP Status:** `403 Forbidden`
- **Error Code:** `recipient_not_allowlisted`
- **Why It Happens:** The API key was provisioned with a strict allowlist (e.g. `@internal.company.com`, `@staging.test`), and the agent attempted to send to an address outside that domain mask.
- **Payload Properties:**
  - `err.recipient`: The recipient email that was rejected.
  - `err.allowlist`: List of string patterns permitted by the key (e.g. `["@internal.company.com"]`).
- **Agent Self-Correction Strategy:**
  1. Do **not** blindly retry the same email.
  2. Read `err.allowlist` to inspect permitted patterns.
  3. Inform the supervisor or calling tool: *"Recipient `foo@external.com` is outside authorized patterns `[@internal.company.com]`. Blocked by server-enforced guardrails."*

---

## 2. Unverified Sending Domain (`DomainNotVerifiedError`)

- **HTTP Status:** `403 Forbidden`
- **Error Code:** `domain_not_verified`
- **Why It Happens:** The sender's domain has not completed DKIM, SPF, or DMARC DNS verification.
- **Payload Properties:**
  - `err.records`: List of DNS records required to achieve alignment.
    ```python
    [
      {
        "type": "TXT",
        "host": "sadasend._domainkey.example.com",
        "value": "v=DKIM1; ...",
        "verdict": "fail", # or "pass", "pending", "inconclusive"
        "note": "DNS record missing or mismatched."
      }
    ]
    ```
- **Agent Self-Correction Strategy:**
  1. Print or pass `err.records` to human operators or DevOps tools to publish the necessary DNS records.
  2. Temporarily route notifications through the verified onboarding domain `noreply@onboarding.sadasend.com` if permitted.

---

## 3. Suppression List Guardrail (`RecipientSuppressedError`)

- **HTTP Status:** `422 Unprocessable Entity`
- **Error Code:** `recipient_suppressed`
- **Why It Happens:** The recipient previously clicked unsubscribe, registered a spam complaint, or experienced a hard bounce.
- **Payload Properties:**
  - `err.recipient`: The blocked address.
  - `err.reason`: `'hard_bounce' | 'complaint' | 'unsubscribe' | 'manual'`
- **Agent Self-Correction Strategy:**
  1. Never retry. Retrying suppressed emails destroys domain reputation and violates CAN-SPAM / GDPR.
  2. Mark the contact as inactive or unsubscribed in your database or agent state.

---

## 4. Deliverability Guardrail Refusal (`UndeliverableRecipientError`)

- **HTTP Status:** `422 Unprocessable Entity`
- **Error Code:** `undeliverable_recipient`
- **Why It Happens:** Triggered when `verify_before_send=True` is passed to `client.emails.send(...)` and the recipient fails real-time MX records validation, syntax rules, or is identified as a disposable burner mailbox. No email credits or monthly quotas are consumed.
- **Payload Properties:**
  - `err.recipient`: The undeliverable recipient email.
  - `err.reason`: Deliverability failure reason (e.g. `mx_missing`, `disposable`, `syntax_invalid`).
  - `err.suggestion`: Suggested typo correction if applicable (e.g. `user@gmail.com` when user entered `user@gmaill.com`).
- **Agent Self-Correction Strategy:**
  1. Inspect `err.suggestion`. If available, ask the user or self-correct to the suggested domain.
  2. If uncorrectable, abort dispatch to prevent bounce rate degradation.

---

## 5. Rate Limiting (`RateLimitError`)

- **HTTP Status:** `429 Too Many Requests`
- **Error Code:** `rate_limit_exceeded` or `account_throttled`
- **Payload Properties:**
  - `err.retry_after_seconds`: Number of seconds specified by the server's `Retry-After` header.
  - `err.is_account_throttle`: `True` if throttled due to global account reputation thresholds.
- **Agent Self-Correction Strategy:**
  1. The SDK automatically sleeps and retries if `retry_after_seconds` is within `max_retry_after_ms` (default: 60s).
  2. If surfaced to your code, schedule a sleep for `err.retry_after_seconds` before resuming operations.

---

## 6. Scope Restrictions (`InsufficientScopeError`)

- **HTTP Status:** `403 Forbidden`
- **Error Code:** `insufficient_scope`
- **Why It Happens:** The API key lacks the required permission scope (e.g., trying to read suppressions with a send-only key).
- **Agent Self-Correction Strategy:**
  1. Do not retry in code. An operator must elevate the key's permissions in the SadaSend dashboard.

---

## 7. Idempotency Key Reused (`IdempotencyKeyReusedError`)

- **HTTP Status:** `409 Conflict`
- **Error Code:** `idempotency_key_reused`
- **Why It Happens:** The agent sent an `idempotency_key` that was already used in a prior request with a different payload body.
- **Agent Self-Correction Strategy:**
  1. Ensure you generate fresh idempotency keys for distinct operations, and reuse keys only when genuinely retrying the exact same email.

---

## 8. Network Disconnects (`ConnectionFailedError`)

- **Type:** Exception (`ConnectionFailedError`)
- **Why It Happens:** Complete network outage, socket timeout, or dropped TLS handshake after exhausting all configured retries.
- **Payload Properties:**
  - `err.cause`: The underlying exception (e.g. `urllib.error.URLError`, `TimeoutError`).
  - `err.attempts`: Number of attempts performed before failure.
- **Agent Self-Correction Strategy:**
  - Because idempotency keys are attached by default, retrying the operation once connectivity returns will never cause duplicate sends.
