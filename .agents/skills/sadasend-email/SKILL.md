---
name: sadasend-email
description: >-
  Use this skill whenever an AI agent needs to dispatch transactional emails,
  perform safe preflight deliverability dry runs, handle recipient allowlists,
  monitor human-in-the-loop approval queues, or verify webhooks using the SadaSend Python SDK.
---

# SadaSend Python SDK — AI Agent Skill

This skill guides autonomous AI agents (Claude, Cursor, LangChain, CrewAI, AutoGen, and Antigravity) on safely and effectively sending transactional emails using the official zero-dependency `sadasend` Python SDK.

Unlike legacy email APIs that blindly dispatch emails or throw generic 400s, SadaSend provides **server-enforced guardrails**, **structured typed exceptions**, and **actionable self-correction metadata** specifically engineered for autonomous agents.

---

## Agent Operating Rules (CRITICAL)

1. **`from_` Keyword Syntax in Python:**
   `from` is a reserved Python language keyword. Always use `from_="noreply@..."` when calling `sadasend.emails.send()`.
2. **`pending_approval` Is a Success, NOT a Failure:**
   When an agent runs under an approval-scoped key (`sada_agent_sk_...`), `result["status"]` will be `'pending_approval'`. This means the email was safely accepted and held in the **Human Approval Queue** for human review in the dashboard. Do **not** treat this as an error or retry.
3. **Use Safe Preflight Dry Runs (`dry_run=True`):**
   Before dispatching a sensitive or bulk email, run with `dry_run=True`. This validates domain verification, recipient allowlists, syntax, and suppression lists at zero cost without emailing external users or consuming quota.
4. **Structured Typed Exceptions — Never Ignore Refusals:**
   In Python, guardrail refusals are raised as typed exceptions inheriting from `SadaSendError`. Always catch `RecipientNotAllowlistedError`, `RecipientSuppressedError`, and `DomainNotVerifiedError` to allow autonomous self-correction.
5. **Always Provide Agent Provenance:**
   Tag all client instances with `default_agent_name="<persona>"` (or pass `agent_name="<persona>"` per send) so system operators can trace velocity, deliverability, and audit logs directly back to your agent.
6. **Always Use Idempotency Keys Across Multi-Step Workflows:**
   Pass `idempotency_key="task-<id>"` to prevent duplicate deliveries during retries, network glitches, or agent loop restarts. The SDK guarantees the exact same key rides every retry attempt.

---

## Quick Reference Workflow

### Step 1: Initialize the Client with Agent Attribution

```python
import os
from sadasend import SadaSend, RetryPolicy

sadasend = SadaSend(
    api_key=os.environ["SADASEND_API_KEY"],
    default_agent_name="customer-support-agent",
    default_source="agent",
    default_channel="sdk",
    timeout=15.0,
    retry=RetryPolicy(max_retries=3),
)
```

### Step 2: Preflight Validation (Safe Dry Run)

```python
from sadasend import RecipientNotAllowlistedError, RecipientSuppressedError, DomainNotVerifiedError

try:
    preflight = sadasend.emails.send(
        from_="notifications@onboarding.sadasend.com",
        to="user@external.com",
        subject="Account Notice",
        text="Preview notice",
        dry_run=True,  # Server evaluates guardrails without dispatching mail
    )
    print("Preflight check passed:", preflight["status"])
except RecipientNotAllowlistedError as err:
    print(f"Preflight blocked: Recipient {err.recipient} outside allowlist {err.allowlist}")
```

### Step 3: Dispatching Real Transactional Emails

```python
import base64
import time

try:
    result = sadasend.emails.send(
        from_="notifications@onboarding.sadasend.com",
        to="alice@company.com",
        subject="Monthly Summary Report",
        html="<h1>Report Ready</h1><p>Your weekly metrics have compiled.</p>",
        text="Report Ready. Your weekly metrics have compiled.",
        tags=["reports", "automated"],
        attachments=[
            {
                "filename": "summary.txt",
                "content": base64.b64encode(b"Report metrics details").decode("utf-8"),
                "contentType": "text/plain",
            }
        ],
        idempotency_key=f"report-run-{int(time.time())}",
    )

    if result["status"] == "pending_approval":
        print(f"Email held safely in Human Approval Queue! ID: {result['id']}")
    else:
        print(f"Email queued for immediate delivery! ID: {result['id']}")
except SadaSendError as err:
    print(f"Send refused by server: [{err.code}] {err.message}")
```

---

## Guardrail Handling & Self-Correction Patterns

Catch specific exceptions to self-correct in autonomous loops:

```python
from sadasend import (
    RecipientNotAllowlistedError,
    DomainNotVerifiedError,
    RecipientSuppressedError,
    RateLimitError,
    ServerError,
    ConnectionFailedError,
)

try:
    send_resp = sadasend.emails.send(
        from_="alerts@onboarding.sadasend.com",
        to=target_recipient,
        subject="Action Required",
        text="Please review your account.",
    )
except RecipientNotAllowlistedError as err:
    # 1. Target is outside key allowlist (e.g. [@acme.com])
    print(f"Cannot reach {err.recipient}. Key is restricted to: {err.allowlist}")
    # Self-correction: Notify supervisor or redirect to internal fallback address

except DomainNotVerifiedError as err:
    # 2. Sending domain lacks DNS records (DKIM/SPF)
    print(f"Sending domain unverified! Missing DNS records: {err.records}")
    # Self-correction: Inform DevOps or route through onboarding.sadasend.com

except RecipientSuppressedError as err:
    # 3. Recipient unsubscribed or hard-bounced
    print(f"Recipient suppressed (reason: {err.reason}). DO NOT RETRY.")
    # Self-correction: Mark contact as inactive in local database

except RateLimitError as err:
    # 4. Key rate limit or account reputation throttle
    print(f"Rate limited. Must wait {err.retry_after_seconds}s before next send.")

except ConnectionFailedError as err:
    # 5. Network down after exhausting all retries
    print(f"Network failure after {err.attempts} attempts: {err.cause}")
```

---

## Verifying Inbound Webhooks

When listening for webhook notifications (`email.delivered`, `email.bounced`, etc.) in web frameworks (FastAPI, Flask, Django):

```python
from sadasend import verify_webhook, parse_webhook

# raw_body MUST be the raw byte string as received over the wire
# In FastAPI: await request.body()
# In Flask: request.get_data()
# In Django: request.body
raw_body = await request.body()
signature_header = request.headers.get("sadasend-signature")
secret = os.environ["SADASEND_WEBHOOK_SECRET"]

event = parse_webhook(secret=secret, body=raw_body, header=signature_header)
if event is None:
    # Signature invalid or expired (> 300s clock drift)
    return {"error": "invalid_signature"}, 400

print(f"Verified webhook event: {event['type']} for message {event['data'].get('messageId')}")
```

---

## References

For deeper references and cheatsheets:
- [Guardrails & Errors Guide](./references/guardrails_and_errors.md)
- [Complete Python SDK Cheatsheet](./references/full_api_cheatsheet.md)
- [Autonomous Agent Execution Pattern Example](./examples/safe_send_with_correction.py)
