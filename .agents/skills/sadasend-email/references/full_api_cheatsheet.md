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

---

## 9. Inbound Email & Context-Safe Parser (`client.inbound`)

```python
# Strip marketing fluff, footers, and extract clean text with prompt-injection defense (~85% token reduction)
parsed = sadasend.inbound.parse(
    raw_mime=raw_eml_string,
    # or pass individual fields:
    # from_="customer@example.com",
    # subject="Order inquiry",
    # text="Can you update my shipping address?",
)
# parsed: {"cleanText": "...", "cleanMarkdown": "...", "extractedTokens": 42, "promptInjectionDetected": False}

# Simulate inbound webhook payload for agent testing
sim = sadasend.inbound.simulate(
    to="support@inbound.yourdomain.com",
    from_="user@example.com",
    subject="Simulation Test",
    text="Test body",
)

# Manage pattern-based MX routing rules (also available via sadasend.inbound_routes)
routes = sadasend.inbound.routes.list()
new_route = sadasend.inbound.routes.create(
    pattern="billing-*@yourdomain.com",
    webhook_url="https://agent.example.com/inbound/billing",
    filter_spam=True,
    strip_signatures=True,
)

# Inspect stored inbound message records (also available via sadasend.inbound_messages)
messages = sadasend.inbound.messages.list(limit=25)
msg = sadasend.inbound.messages.get("inb_msg_123")
```

---

## 10. DMARC Deliverability Radar (`client.dmarc`)

```python
# Retrieve deliverability scorecard, alignment rates, and policy upgrade advice (p=none -> p=reject)
summary = sadasend.dmarc.summary(domain="yourdomain.com", days=30)
# summary: {"domain": "yourdomain.com", "alignment": 99.4, "currentPolicy": "p=reject", "recommendation": "..."}

# Forensic threat analysis and unauthorized spoofing sources
threats = sadasend.dmarc.threats(domain="yourdomain.com")
# threats: {"threats": [{"ip": "198.51.100.4", "source": "unauthorized_relay", "count": 14}]}

# Ingest and query aggregate RFC 7489 feedback XML reports (also available via sadasend.dmarc_reports)
reports = sadasend.dmarc.reports.list(domain="yourdomain.com", limit=20)
report = sadasend.dmarc.reports.get("dmarc_rep_123")
new_report = sadasend.dmarc.reports.create(xml="<feedback>...</feedback>")
```

---

## 11. Multi-Agent Collision Arbiter (`client.arbiter`)

```python
# System-wide cross-agent collision telemetry & prevented message loops
stats = sadasend.arbiter.stats()
# stats: {"active_cooldowns": 3, "held_tickets": 1, "collisions_prevented_24h": 42}

# Inspect recipient cooldown status (also available via sadasend.arbiter_recipients)
status = sadasend.arbiter.cooldowns.status("customer@example.com")
# status: {"in_cooldown": True, "expires_at": "...", "agent_name": "support-bot"}

# Set quiet period cooldown for recipient across all agents
sadasend.arbiter.cooldowns.set_cooldown(
    recipient="customer@example.com",
    cooldown_seconds=3600,
    priority="high",
    agent_name="billing-agent",
)

# Clear cooldown manually when conversation completes
sadasend.arbiter.cooldowns.clear_cooldown("customer@example.com")

# Hold agent delivery while support ticket is open (also available via sadasend.arbiter_tickets)
sadasend.arbiter.tickets.create(
    recipient="customer@example.com",
    ticket_id="TICK-8841",
    subject="Billing Dispute Escalation",
)
sadasend.arbiter.tickets.delete("customer@example.com")
```

---

## 12. Multi-Agent Ephemeral Inboxes (`client.inboxes`)

```python
# Provision disposable sub-10ms inbox for agent signups or 2FA workflows
inbox = sadasend.inboxes.create_ephemeral(
    alias="test-agent-flow",
    ttl_seconds=300,
    description="Agent auth verification",
)
# inbox: {"id": "inb_agent_xyz", "address": "test-agent-flow@sadasend.dev", "expires_at": "..."}

# Direct OTP extraction with server-side polling / regex parsing
otp_result = sadasend.inboxes.otp(
    inbox["id"],
    timeout_ms=10000,
)
# otp_result: {"code": "849201", "message_id": "msg_otp_99"}

# Retrieve received emails in ephemeral inbox
msgs = sadasend.inboxes.messages(inbox["id"])

# Delete disposable inbox when workflow concludes
sadasend.inboxes.delete(inbox["id"])
```

---

## 13. Testing Sandbox (`client.testing`)

```python
# Ingest synthetic email into test environment
sadasend.testing.inbound(
    to="qa-agent@sandbox.sadasend.dev",
    from_="auth-system@example.com",
    subject="Your Verification Code: 994821",
    text="Use 994821 to log into your account.",
)

# Wait for 2FA / verification code with timeout (also available via sadasend.testing.wait_for_code)
code_data = sadasend.testing.waitForCode(
    to="qa-agent@sandbox.sadasend.dev",
    timeout_ms=15000,
)
# code_data: {"code": "994821", "found": True}

# Direct test inboxes inspection (also available via sadasend.testing_inboxes)
latest_email = sadasend.testing.inboxes.latest("qa-agent@sandbox.sadasend.dev")
```

---

## 14. Integrations, Team & Support Governance

```python
# 1-Click Slack interactive approvals configuration status
slack_status = sadasend.integrations.slack()
# slack_status: {"connected": True, "channel": "#agent-email-approvals"}

# Enumerate team members, roles, and ownership
team = sadasend.team.get()
# team: {"members": [{"email": "owner@company.com", "role": "owner"}, ...]}

# List support tickets and conversations
tickets = sadasend.support_tickets.list()
```
