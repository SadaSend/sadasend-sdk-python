# sadasend

[![PyPI version](https://img.shields.io/pypi/v/sadasend.svg)](https://pypi.org/project/sadasend/)
[![Python versions](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://pypi.org/project/sadasend/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/SadaSend/sadasend-sdk-python/blob/main/LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0%20(stdlib%20only)-success.svg)](https://pypi.org/project/sadasend/)
[![Tests Passing](https://img.shields.io/badge/tests-66%20passed-brightgreen.svg)](https://github.com/SadaSend/sadasend-sdk-python)
[![Typing: Typed](https://img.shields.io/badge/typing-typed-blue.svg)](https://pypi.org/project/sadasend/)

The official Python SDK for [SadaSend](https://sadasend.com) — high-throughput transactional email with unbypassable server-enforced guardrails designed for human software engineering teams and autonomous AI agents.

**Zero external dependencies.** Built strictly on the Python standard library (`urllib.request`, `hmac`, `hashlib`, `json`). No transitive dependencies, no version pinning conflicts, no vulnerability CVE alerts, and zero supply-chain risk.

---

## Why SadaSend?

Legacy email APIs (SendGrid, Mailgun, Postmark, AWS SES) were built for human backends. When you hand an API key to an autonomous LLM agent (LangChain, CrewAI, AutoGen, Claude Code, Cursor), a hallucination or prompt injection can blast spam or burn your sending domain reputation. SadaSend is built from day one with **unbypassable server-enforced guardrails**.

| Feature | SadaSend | SendGrid | Mailgun | Postmark | AWS SES |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Runtime Dependencies** | **0 (Standard Library Only)** | 8+ dependencies | requests / urllib3 | requests | boto3 (heavy) |
| **Agent Recipient Allowlist** | **Server-Enforced** | None (Manual) | None | None | None |
| **Human Approval Mode** | **Native (`pending_approval`)** | None | None | None | None |
| **Built-in Idempotency** | **Automatic (Guaranteed Replay)** | None | Manual | None | None |
| **Retry-After Backoff** | **Automatic Full Jitter** | Manual | Naive | Manual | Manual |
| **Native MCP Server** | **Native (`POST /mcp`)** | None | None | None | None |
| **Typed Exceptions with Fixes** | **Yes (`records`, `allowlist`)** | Generic HTTP 400 | Generic HTTP 400 | Generic HTTP 422 | Generic ClientError |
| **Preflight Dry Runs** | **Native (`dry_run=True`)** | None | None | None | None |

---

## Installation

```bash
# pip
pip install sadasend

# poetry
poetry add sadasend

# uv
uv add sadasend
```

Works out of the box on Python 3.9, 3.10, 3.11, 3.12, and 3.13. Ideal for serverless environments (AWS Lambda, Google Cloud Functions, Cloudflare Python Workers) and Docker micro-containers due to zero external package installation footprint.

---

## 10-Line Quickstart

```python
import os
from sadasend import SadaSend

sadasend = SadaSend(os.environ["SADASEND_API_KEY"])

result = sadasend.emails.send(
    from_="noreply@onboarding.sadasend.com",
    to="dana@example.com",
    subject="Hello from Python",
    html="<strong>Transactional email with zero dependencies.</strong>",
)

print(result["status"], result["id"])
```

> **Note:** `from_` has a trailing underscore because `from` is a reserved Python keyword.

---

## Autonomous AI Agent Safety: The Server-Enforced Moat

Granting an autonomous agent email capability creates a real blast radius. SadaSend solves this with **Server-Side Ceilings**:

```text
  ┌────────────────────────────────────────────────────────┐
  │  Human Engineer Mints Key in Dashboard / Admin Ops     │
  │  {                                                     │
  │    scopes: ["send", "read"],    # What it may do       │
  │    allowlist: ["@acme.com"],    # Who it may reach     │
  │    rate_limit: "50 / 1h",       # Max rate ceiling     │
  │    mode: "approval"             # Human in the loop    │
  │  }                                                     │
  └──────────────────────────┬─────────────────────────────┘
                             │ Mints sada_agent_sk_...
                             ▼
  ┌────────────────────────────────────────────────────────┐
  │  Autonomous Agent Python Code / LangChain / CrewAI     │
  │  client = SadaSend(os.environ["SADASEND_AGENT_KEY"])   │
  │                                                        │
  │  ❌ Agent CANNOT widen allowlist or edit its scopes    │
  │  ❌ Agent CANNOT mint new keys (session-only endpoint) │
  │  ❌ Agent CANNOT approve its own held mail             │
  └────────────────────────────────────────────────────────┘
```

### The 4 Pillars of Agent Safety

1. **Recipient Allowlists**: If an agent attempts to email an unauthorized domain or address, the server intercepts the request before it leaves the outbox, raising `RecipientNotAllowlistedError`.
2. **Human Approval Mode (`mode: "approval"`)**: Keys prefixed with `sada_agent_sk_` route outgoing mail to `status = "pending_approval"`. The email is held safely in the Human Approval Queue until a teammate approves it in the dashboard.
3. **Hard Rate Limit Ceilings**: Per-key quotas stop recursive runaway loops with `RateLimitError` (HTTP 429).
4. **Preflight Dry-Runs (`dry_run=True`)**: Agents validate rendering, SPF/DKIM verification, and suppression status without dispatching real mail.

```python
import os
from sadasend import SadaSend, RecipientNotAllowlistedError

# Initialized with an agent-scoped key (sada_agent_sk_...)
agent_client = SadaSend(os.environ["SADASEND_AGENT_KEY"])

# 1. Safe Preflight Dry Run: Validates deliverability without sending
preview = agent_client.emails.send(
    from_="noreply@notifications.sadasend.com",
    to="partner@acme.com",
    subject="Quarterly Summary",
    html="<h1>Summary</h1>",
    dry_run=True,
)
print("Dry run validated:", preview["status"])

# 2. Live Send under Human Approval Mode
try:
    result = agent_client.emails.send(
        from_="noreply@notifications.sadasend.com",
        to="partner@acme.com",
        subject="Contract Proposal",
        html="<p>Please review attached contract.</p>",
    )
    if result["status"] == "pending_approval":
        # Safe! The email is held for human sign-off in the dashboard.
        print(f"Message held for human approval. ID: {result['id']}")
except RecipientNotAllowlistedError as e:
    # Model inspects refusal and self-corrects
    print(f"Refused: Recipient {e.recipient} not in allowlist {e.allowlist}")
```

---

## Agent Provenance Tracking

Track exactly which autonomous agent, pipeline, or model generated each outgoing message:

```python
# Option A: Client-level provenance
client = SadaSend(
    api_key=os.environ["SADASEND_API_KEY"],
    default_agent_name="billing-reconciliation-bot",
    default_source="agent",
    default_channel="sdk",
)

# Option B: Per-request provenance
result = client.emails.send(
    from_="noreply@yourdomain.com",
    to="customer@example.com",
    subject="Monthly Invoice",
    html="<p>Your invoice is ready.</p>",
    agent_name="billing-reconciliation-bot",
    source="agent",
    channel="sdk",
)
```

Telemetry is visible on the dashboard and via `client.account.stats(provenance=True)`.

---

## Core Features Walkthrough

### 1. Advanced Transactional Sends (Attachments, CC, BCC, Tags, Headers)

```python
import base64

pdf_data = base64.b64encode(b"%PDF-1.4 sample content...").decode("utf-8")

result = sadasend.emails.send(
    from_="Billing Team <billing@yourdomain.com>",
    to=["customer@example.com"],
    cc=["finance@yourdomain.com"],
    bcc=["archive@yourdomain.com"],
    reply_to="support@yourdomain.com",
    subject="Invoice #INV-2026-08",
    html="<h1>Your Invoice is Ready</h1><p>Thank you for your business!</p>",
    text="Your Invoice is Ready. Thank you for your business!",
    tags=["billing", "invoices"],
    headers={"X-Entity-Ref-ID": "INV-2026-08"},
    attachments=[{
        "filename": "invoice.pdf",
        "content": pdf_data,
        "contentType": "application/pdf",
    }],
    idempotency_key="invoice-send-INV-2026-08",
)
```

### 2. High-Efficiency Batch Sends (`emails.batch`)

Send up to 100 emails in a single atomic HTTP request with RFC 4918 Multi-Status results:

```python
batch = sadasend.emails.batch(emails=[
    {
        "from": "updates@yourdomain.com",
        "to": "alice@example.com",
        "subject": "System Update v2.0",
        "text": "Hi Alice, version 2.0 is live!",
    },
    {
        "from": "updates@yourdomain.com",
        "to": "bob@example.com",
        "subject": "System Update v2.0",
        "text": "Hi Bob, version 2.0 is live!",
    },
])

print(f"Batch processed: {batch["total"]} messages queued.")
for item in batch["results"]:
    print(f"Recipient: {item.get("to")}, Status: {item.get("status")}")
```

### 3. Retrieve, Resend, and Cancel Scheduled Emails

```python
# Inspect message delivery state
message = sadasend.emails.get("msg_01hy7q8v")
print(f"Status: {message["status"]}, Delivered at: {message.get("deliveredAt")}")

# Resend an existing message under original parameters
resend = sadasend.emails.resend("msg_01hy7q8v")

# Cancel a scheduled email before dispatch
future_email = sadasend.emails.send(
    from_="reminders@yourdomain.com",
    to="user@example.com",
    subject="Upcoming Appointment",
    text="Don't forget your appointment tomorrow!",
    scheduled_at="2026-11-01T09:00:00Z",
)
cancel_result = sadasend.emails.cancel(future_email["id"])
print("Cancelled status:", cancel_result["status"])
```

### 4. Template Rendering & Live Testing (`templates`)

Store templates server-side with Liquid syntax:

```python
# List available templates
templates = sadasend.templates.list()

# Render template with variables without sending
rendered = sadasend.templates.render(
    id_="tpl_welcome",
    variables={"name": "Alex", "verification_link": "https://example.com/verify?token=123"},
)
print("Preview HTML:", rendered["html"])

# Send a live test email using template
test_send = sadasend.templates.test(
    id_="tpl_welcome",
    to="qa@yourdomain.com",
    variables={"name": "Alex QA"},
)
```

### 5. Sending Domains Management & DNS Verification (`domains`)

```python
# List sending domains
domains = sadasend.domains.list()

# Get required DNS records (SPF, DKIM, DMARC)
dns = sadasend.domains.records("dom_01hy7q8v")
for record in dns["records"]:
    print(f"[{record["type"]}] {record["host"]} -> {record["value"]} ({record["status"]})")

# Trigger live DNS verification check
verification = sadasend.domains.verify("dom_01hy7q8v")
print("Verification status:", verification["status"])
```

### 6. Suppression List Management (`suppressions`)

```python
# Enumerate suppressed recipients
suppressions = sadasend.suppressions.list(limit=50, reason="unsubscribe")

# Manually add address to suppression list
sadasend.suppressions.add(
    address="unsub@example.com",
    reason="manual",
)
```

### 7. Account Health & Deliverability Telemetry (`account`)

```python
# Plan & monthly quota telemetry
acc = sadasend.account.get()
print(f"Plan: {acc['plan']}, Quota: {acc['emailsUsed']} / {acc['emailQuota']}")

# 14-day deliverability metrics
stats = sadasend.account.stats(window="14d")
print(f"Delivered: {stats['delivered']}, Bounce Rate: {stats['bounceRate']}%, Complaint Rate: {stats['complaintRate']}%")

# Daily volume distribution
vol = sadasend.account.volume(window="7d")
for day in vol["days"]:
    print(f"{day['date']}: {day['count']} sent")
```

### 8. Deliverability Verification Shield & Pre-Send Validation

Protect sender reputation and verify recipient deliverability in real time without burning sending quota:

```python
# 1. Standalone single email verification
verification = sadasend.tools.verify(email="alex@example.com")
print(f"Status: {verification['status']}, Score: {verification['score']}/100, Reason: {verification.get('reason')}")

# 2. Batch deliverability verification
batch_ver = sadasend.tools.verify_batch(emails=[
    "valid@startup.io",
    "bounced@disposable.org",
    "invalid-syntax@bad",
])
print(f"Total: {batch_ver['total']}, Deliverable: {batch_ver['deliverable']}")

# 3. Send-time deliverability shield: refuses undeliverable recipients with 422 before queueing
result = sadasend.emails.send(
    from_="alerts@yourdomain.com",
    to="newuser@example.com",
    subject="Welcome to our platform",
    text="Your account is active.",
    verify_before_send=True,  # Instant MX, disposable, and syntax verification
    marketing=True,           # Injects RFC 8058 One-Click List-Unsubscribe headers
)
```

### 9. Standardized UTM Campaign URL Normalization (`tools.utm`)

Normalize and inject UTM campaign parameters into destination URLs on the fly:

```python
utm_result = sadasend.tools.utm(
    url="https://yourdomain.com/pricing?ref=partner#enterprise",
    source="newsletter",
    medium="email",
    campaign="q4_feature_launch",
    term="transactional",
    content="cta_button",
)
print("Normalized URL:", utm_result["url"])
# Preserves query parameters and anchor (#enterprise)
```

### 10. Prepaid Credit Packs & Paddle Checkout (`billing.credits_checkout`)

Initialize a Paddle checkout transaction for prepaid verification or sending credit packs:

```python
checkout = sadasend.billing.credits_checkout(
    pack="25k",         # "5k", "25k", "100k", "500k" for verify; "10k", "50k", "100k" for send
    type="verify",      # "verify" | "send"
    return_url="https://yourdomain.com/dashboard/billing",
)
print(f"Transaction: {checkout['transactionId']}, URL: {checkout['checkoutUrl']}")
```

---

## Cryptographic HMAC Webhook Verification

Verify inbound delivery, bounce, and complaint webhooks using standard library only (`hmac`, `hashlib`).

### FastAPI

```python
import os
from fastapi import FastAPI, Request, HTTPException
from sadasend import parse_webhook

app = FastAPI()
WEBHOOK_SECRET = os.environ["SADASEND_WEBHOOK_SECRET"]

@app.post("/webhooks/sadasend")
async def handle_sadasend_webhook(request: Request):
    # CRITICAL: Read raw body bytes. json.loads() roundtrips alter whitespace/key order.
    raw_body = await request.body()
    signature = request.headers.get("sadasend-signature")

    event = parse_webhook(
        secret=WEBHOOK_SECRET,
        body=raw_body,
        header=signature,
    )
    if not event:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    event_type = event["type"]
    msg_id = event["data"].get("messageId")
    print(f"Received {event_type} for message {msg_id}")

    return {"received": True}
```

### Flask

```python
import os
from flask import Flask, request, jsonify
from sadasend import parse_webhook

app = Flask(__name__)
WEBHOOK_SECRET = os.environ["SADASEND_WEBHOOK_SECRET"]

@app.post("/webhooks/sadasend")
def handle_sadasend_webhook():
    raw_body = request.get_data()
    signature = request.headers.get("sadasend-signature")

    event = parse_webhook(
        secret=WEBHOOK_SECRET,
        body=raw_body,
        header=signature,
    )
    if not event:
        return jsonify({"error": "Invalid webhook signature"}), 400

    return jsonify({"received": True}), 200
```

### Django

```python
import os
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from sadasend import parse_webhook

WEBHOOK_SECRET = os.environ["SADASEND_WEBHOOK_SECRET"]

@csrf_exempt
def sadasend_webhook_view(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    raw_body = request.body
    signature = request.headers.get("sadasend-signature")

    event = parse_webhook(
        secret=WEBHOOK_SECRET,
        body=raw_body,
        header=signature,
    )
    if not event:
        return JsonResponse({"error": "Invalid webhook signature"}, status=400)

    return JsonResponse({"received": True})
```

- **Replay Protection**: Timestamps are cryptographically signed with the body and expire after 5 minutes.
- **Timing-Attack Immune**: Comparison uses `hmac.compare_digest` to prevent byte-at-a-time timing attacks.

---

## Typed Exceptions & Error Handling

In Python, an unexamined return value allows a program to silently continue as though mail went out. SadaSend **raises specific typed exceptions** carrying actionable remediation payloads:

```python
from sadasend import (
    SadaSend,
    DomainNotVerifiedError,
    RecipientNotAllowlistedError,
    RecipientSuppressedError,
    RateLimitError,
)

try:
    result = sadasend.emails.send(
        from_="billing@yourdomain.com",
        to="client@example.com",
        subject="Monthly Invoice",
        html="<p>Invoice attached</p>",
    )
except DomainNotVerifiedError as e:
    # Remediation DNS records are attached directly to the exception
    print("Domain is not verified. Please configure these DNS records:")
    for record in e.records:
        print(f"  {record["type"]} {record["host"]} -> {record["value"]}")
except RecipientNotAllowlistedError as e:
    print(f"Agent key blocked: {e.recipient} is not in allowlist {e.allowlist}")
except RecipientSuppressedError as e:
    print(f"Cannot send to {e.recipient}: suppressed due to previous {e.reason}")
except RateLimitError as e:
    print(f"Rate limited. Obey retry_after_seconds: {e.retry_after_seconds}s")
```

### Exception Hierarchy

| Exception Class | Trigger Cause | Auto-Retried? | Attached Payload Attributes |
| :--- | :--- | :---: | :--- |
| `AuthenticationError` | API key invalid, revoked, or missing | No | `code`, `status`, `message` |
| `InsufficientScopeError` | Key lacks required scope (`send`, `read`, etc.) | No | `code`, `status`, `message` |
| `InvalidFromError` | Malformed or invalid sender email address | No | `code`, `status`, `message` |
| `DomainNotFoundError` | Domain not registered on this account | No | `code`, `status`, `message` |
| `DomainNotVerifiedError` | Sending domain failed SPF/DKIM verification | No | `records` (List of required DNS entries) |
| `RecipientNotAllowlistedError` | Agent key attempted to email unauthorized address | No | `recipient`, `allowlist` |
| `RecipientSuppressedError` | Recipient previously unsubscribed or bounced | No | `recipient`, `reason` |
| `IdempotencyKeyReusedError` | Same idempotency key used with different payload | No | `code`, `status`, `message` |
| `IdempotencyInProgressError` | Initial request with this key is still processing | **Yes** | `code`, `status`, `message` |
| `RateLimitError` | Key or account rate limit exceeded (HTTP 429) | **Yes** | `retry_after_seconds`, `is_account_throttle` |
| `ServerError` | Transient 5xx upstream server error | **Yes** | `status`, `message` |
| `ConnectionFailedError` | Network timeout, socket drop, or DNS failure | **Yes** | `cause`, `attempts` |
| `UndeliverableRecipientError` | Pre-send verification failure (`verify_before_send=True`) | No | `recipient`, `reason`, `suggestion` |
| `InvalidSubjectError` | Subject violates RFC 5322 length (> 998 chars) or forbidden control chars | No | `code`, `status`, `message` |
| `InvalidDateError` | `scheduled_at` date is in past or beyond max 72-hour window | No | `code`, `status`, `message` |
| `BatchSizeExceededError` | Batch send exceeds 100 emails limit | No | `code`, `status`, `message` |
| `PlanTierInsufficientError` | Feature or limit requires upgrading plan | No | `code`, `status`, `message` |
| `AnonymousLimitExceededError` | Free unauthenticated deliverability check limit reached (5/day) | No | `code`, `status`, `message` |
| `InvitationAlreadyPendingError` | Team invitation already pending for recipient | No | `code`, `status`, `message` |
| `InvalidPlanError` | Invalid plan or pack selected for checkout | No | `code`, `status`, `message` |

---

## Idempotency & Automatic Retries

Every mutating request carries an `Idempotency-Key` header. The SDK provides:
1. **Zero Duplicate Sends**: The exact same `Idempotency-Key` rides every retry attempt across network drops.
2. **Full Jitter Exponential Backoff**: Transient errors (5xx, HTTP 429, socket drops) are retried with randomized jitter to prevent thundering herds.
3. **Respect for `Retry-After`**: The client waits the exact duration specified by the server instead of guessing.
4. **Custom Keys**: Pass `idempotency_key="order_1234"` to guarantee exactly-once delivery across server restarts:

```python
sadasend.emails.send(
    from_="orders@yourdomain.com",
    to="customer@example.com",
    subject="Order Confirmation #1234",
    html="<p>Thank you for your order!</p>",
    idempotency_key=f"order-confirmation-1234",
)
```

---

## Complete API Reference (All 11 Resources)

| Resource | Operation | Description |
| :--- | :--- | :--- |
| `client.emails` | `send(...)` | Send transactional email with attachments, tags, dry run, or approval mode. |
| `client.emails` | `batch(...)` | Send up to 100 emails in an atomic HTTP batch request. |
| `client.emails` | `get(id_)` | Retrieve delivery state and timeline for a sent message. |
| `client.emails` | `list(...)` | Enumerate sent messages with filtering by status, tag, or recipient. |
| `client.emails` | `resend(id_)` | Resend a previously queued or sent email. |
| `client.emails` | `cancel(id_)` | Cancel a scheduled email before dispatch. |
| `client.domains` | `list()` | List all sending domains registered on the account. |
| `client.domains` | `records(id_)` | Retrieve SPF, DKIM, and DMARC DNS record requirements. |
| `client.domains` | `verify(id_)` | Run a live internet DNS check to verify domain records. |
| `client.templates` | `list()` | Enumerate all stored email templates. |
| `client.templates` | `get(id_)` | Fetch template details including Liquid markup. |
| `client.templates` | `render(id_, ...)` | Render template against variables without dispatching email. |
| `client.templates` | `test(id_, ...)` | Send a test email rendering a template. |
| `client.suppressions` | `list(...)` | Enumerate unsubscribed, bounced, or complained addresses. |
| `client.suppressions` | `add(...)` | Add an email address to the account suppression list. |
| `client.account` | `get()` | Retrieve account details, current plan, and monthly send quotas. |
| `client.account` | `stats(...)` | Deliverability telemetry (delivered, bounce rate, complaint rate). |
| `client.account` | `volume(...)` | Daily volume trend breakdown across 7d, 14d, or 30d windows. |
| `client.account` | `circuit_breakers()` | Check active deliverability circuit breaker thresholds. |
| `client.account` | `checklist()` | Onboarding deliverability checklist items. |
| `client.account` | `staff_access(...)` | View customer support and staff audit access grants. |
| `client.keys` | `list()` | Enumerate API keys on the account. |
| `client.keys_approvals`| `list()` | Enumerate held emails awaiting human approval. |
| `client.support_tickets`| `list()`, `get(id_)` | View support tickets and communications. |
| `client.team` | `get()` | Enumerate team members, owners, and roles. |
| `client.tools` | `list()`, `check(...)` | Run free unauthenticated deliverability checks (SPF, DKIM, DMARC, DNS). |
| `client.webhooks` | `list()`, `deliveries(...)` | View webhook endpoints and delivery attempt logs. |

---

## Native Model Context Protocol (MCP)

Building with **Claude Code**, **Cursor**, **Windsurf**, or custom LLM agent tools? SadaSend features a native Model Context Protocol (MCP) server at `POST /mcp`.

Add SadaSend directly to your agent config:

```json
{
  "mcpServers": {
    "sadasend": {
      "url": "https://api.sadasend.com/mcp",
      "headers": {
        "Authorization": "Bearer sada_agent_sk_your_key_here"
      }
    }
  }
}
```

Learn more in our [Model Context Protocol Guide](https://sadasend.com/docs/mcp).

---

## Frequently Asked Questions (FAQ)

### Does `sadasend` require any external third-party dependencies?
**No.** `sadasend` has **zero external runtime dependencies**. It is built entirely on the Python standard library (`urllib.request`, `hmac`, `hashlib`, `json`). This means no supply-chain vulnerabilities, zero CVE alerts, zero package conflicts with `requests` or `urllib3`, and lightning-fast cold starts in AWS Lambda and Docker.

### How does SadaSend prevent autonomous AI agents from sending rogue emails?
SadaSend enforces guardrails on the server:
1. **Recipient Allowlists**: Keys can be restricted to specific domains (e.g. `@acme.com`). Attempts to email unauthorized addresses are blocked with `RecipientNotAllowlistedError`.
2. **Human Approval Mode**: Agent keys (`sada_agent_sk_...`) can route outgoing emails to `status = "pending_approval"`, requiring a human teammate to click approve in the dashboard.
3. **Hard Rate Limit Ceilings**: Prevents runaway recursive agent loops from exhausting budgets.

### How does idempotency protect against duplicate sends?
Every request automatically generates a unique `Idempotency-Key` UUID. If a network connection drops mid-flight and the SDK retries, it sends the exact same key. The SadaSend server detects the duplicate and returns the original response without sending a second email.

### Can I use SadaSend with Celery, RQ, or background threads?
**Yes.** The `SadaSend` client is stateless and thread-safe. You can initialize a single client instance and share it across threads or instantiate it inside worker tasks.

### What Python versions are supported?
Python 3.9, 3.10, 3.11, 3.12, and 3.13 are fully supported and verified in CI.

---

## Canonical Resources

- **Official Website**: [https://sadasend.com](https://sadasend.com)
- **API Documentation**: [https://sadasend.com/docs](https://sadasend.com/docs)
- **Pricing & Plans**: [https://sadasend.com/pricing](https://sadasend.com/pricing)
- **Model Context Protocol (MCP)**: [https://sadasend.com/docs/mcp](https://sadasend.com/docs/mcp)
- **Developer Support**: [support@sadasend.com](mailto:support@sadasend.com)

---

## License

MIT © [SadaSend](https://sadasend.com)
