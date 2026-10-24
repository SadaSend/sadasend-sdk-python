# SadaSend Python SDK Cheatsheet for AI Agents

All methods on the `SadaSend` client return standard Python dictionaries (`Dict[str, Any]`), and guardrail refusals or HTTP errors raise typed subclasses of `SadaSendError`.

---

## 1. Emails (`client.emails`)

```python
# Send single email
res = sadasend.emails.send(
    from_="alerts@domain.com",       # Required (trailing underscore for Python)
    to="user@example.com",           # str or List[str]
    cc="colleague@example.com",      # Optional str or List[str]
    bcc="audit@example.com",         # Optional str or List[str]
    reply_to="help@domain.com",      # Optional str or List[str]
    subject="Invoice Ready",
    html="<p>HTML body</p>",
    text="Plain text body",
    template="tmpl_123",             # Stored template id or name
    variables={"name": "Alice"},
    tags=["billing", "october"],
    headers={"X-Entity-ID": "inv_99"},
    attachments=[
        {
            "filename": "receipt.pdf",
            "content": base64_content,
            "contentType": "application/pdf",
        }
    ],
    scheduled_at="2026-11-01T12:00:00Z", # Future ISO timestamp
    dry_run=True,                        # Zero-cost preflight validation
    verify_before_send=True,             # Real-time sub-50ms MX/syntax/disposable verification before queuing
    marketing=True,                      # Injects RFC 8058 one-click List-Unsubscribe headers
    utm={                                # Standardized campaign tracking parameters
        "source": "agent_billing",
        "medium": "email",
        "campaign": "q4_renewal",
    },
    idempotency_key="order-1234",        # Custom domain idempotency key
    channel="sdk",                       # 'api' | 'sdk' | 'mcp' | 'smtp' | 'console'
    source="agent",                      # 'backend' | 'agent' | 'automation' | 'system'
    agent_name="billing-bot",            # Attributed agent identifier
)
# res: {"id": "msg_123", "status": "queued" | "pending_approval", ...}

# Retrieve message status & event trail
msg = sadasend.emails.get("msg_123")
# msg: {"id": "msg_123", "status": "delivered", "to": [...], "events": [...]}

# Resend under original key
resend = sadasend.emails.resend("msg_123")

# Cancel scheduled message before dispatch
cancelled = sadasend.emails.cancel("msg_123")

# List recent emails with filters
emails_list = sadasend.emails.list(
    limit=20,
    agent_name="billing-bot",
    status="delivered", # 'queued' | 'sent' | 'delivered' | 'bounced' | 'complained' | 'pending_approval'
    q="invoice",
    cursor="cur_next",
)

# High-throughput batch sending (RFC 4918 Multi-Status)
batch = sadasend.emails.batch([
    {"from": "a@d.com", "to": "u1@d.com", "subject": "1", "text": "hi"},
    {"from": "a@d.com", "to": "u2@d.com", "subject": "2", "text": "hi"},
])
# batch: {"total": 2, "accepted": 2, "refused": 0, "results": [...]}
```

---

## 2. Account Telemetry & Quotas (`client.account`)

```python
# Plan, state, and usage quotas
info = sadasend.account.get()
# info: {"org": "...", "plan": "growth", "emailsUsed": 150, "emailQuota": 10000, "reputationLevel": "optimal"}

# Deliverability statistics
stats = sadasend.account.stats(window="14d")
# stats: {"sent": 1200, "delivered": 1198, "deliveryRate": 0.998, "bounceRate": 0.001}

# Daily volume sparkline
volume = sadasend.account.volume(window="7d")
# volume: {"days": [{"date": "2026-10-09", "count": 250}, ...]}

# Onboarding checklist
checklist = sadasend.account.checklist()
# checklist: {"items": [{"key": "domain_verified", "completed": True}, ...]}

# Autonomous agent velocity circuit breakers
breakers = sadasend.account.circuit_breakers()

# Staff access transparency logs
staff = sadasend.account.staff_access(limit=10)
```

---

## 3. Domains & DNS Verification (`client.domains`)

```python
# List sending domains
domains = sadasend.domains.list()

# Get required DNS records (SPF, DKIM, DMARC)
records = sadasend.domains.records(domain_id)

# Trigger on-demand DNS verification check
verify = sadasend.domains.verify(domain_id)
```

---

## 4. Templates (`client.templates`)

```python
# List templates
templates = sadasend.templates.list()

# Get one template with bodies
template = sadasend.templates.get("tmpl_123")

# Server-side render with test variables (no send)
rendered = sadasend.templates.render("tmpl_123", variables={"name": "Alice"})

# Send test preview email
test_resp = sadasend.templates.test("tmpl_123", to="qa@company.com", variables={"name": "Alice"})
```

---

## 5. Suppressions (`client.suppressions`)

```python
# Add address to suppression list
added = sadasend.suppressions.add("unsub@example.com", reason="unsubscribe")
# reason: 'unsubscribe' | 'complaint' | 'hard_bounce' | 'manual'

# Search suppressions
suppressed = sadasend.suppressions.list(q="unsub@example.com", limit=25)
```

---

## 6. Approvals & Governance (`client.keys_approvals` & `client.keys`)

```python
# List outgoing sends held in Human Approval Queue awaiting sign-off
approvals = sadasend.keys_approvals.list()
# approvals: {"approvals": [{"id": "...", "to": ["..."], "subject": "..."}]}

# List API keys
keys = sadasend.keys.list()
```

---

## 7. Deliverability Tools (`client.tools`)

```python
# List free diagnostic checks
tools_list = sadasend.tools.list()

# Run deliverability check (SPF, DKIM, MX, DMARC)
check_result = sadasend.tools.check(check="dkim", subject="mycompany.com", selector="sadasend")

# Real-time recipient deliverability verification (sub-50ms)
verified = sadasend.tools.verify(email="user@example.com")
# verified: {"email": "...", "status": "deliverable", "score": 98, "verdict": "pass"}

# High-throughput batch email deliverability verification
batch_verified = sadasend.tools.verify_batch(emails=["alex@example.com", "sam@example.com"])
# batch_verified: {"ok": True, "total": 2, "deliverable": 2, ...}

# Normalize and inject campaign UTM tracking parameters into URLs
tagged_url = sadasend.tools.utm(
    url="https://example.com/checkout",
    source="agent_claude",
    medium="email",
    campaign="onboarding",
)
```

---

## 8. Webhook Endpoints & Deliveries (`client.webhooks`)

```python
# List configured webhook endpoints
endpoints = sadasend.webhooks.list()

# Inspect delivery attempts for an endpoint
deliveries = sadasend.webhooks.deliveries("wh_123", limit=20)
```
