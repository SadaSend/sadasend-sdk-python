#!/usr/bin/env python3
"""
SadaSend Python SDK — Full Features Walkthrough

This example demonstrates the complete capabilities of SadaSend in Python:
1. Client initialization with custom timeouts & retry policies
2. Advanced transactional sending (HTML, text, CC, BCC, Reply-To, tags, headers, attachments)
3. Idempotency guarantees & preflight dry runs (`dry_run=True`)
4. Scheduled sending & atomic cancellation
5. High-efficiency batch email dispatch with per-item Multi-Status evaluation
6. Email resend under originating key
7. Idiomatic Python exception handling with actionable guardrail remediation
8. Server-side template rendering with Liquid variables
9. Sending domains management & on-demand DNS verification
10. Suppression list management (add & search)
11. Account observability, quotas, deliverability stats & volume sparklines
12. Webhook endpoints & constant-time HMAC-SHA256 signature verification

Run this example:
  SADASEND_API_KEY="your_api_key" python3 examples/full_features.py
"""

from __future__ import annotations

import base64
import datetime
import hashlib
import hmac
import json
import os
import sys
import time
from pathlib import Path

# Add sadasend package to sys.path so it imports the local package directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sadasend import (
    SadaSend,
    RetryPolicy,
    DomainNotVerifiedError,
    RecipientNotAllowlistedError,
    RecipientSuppressedError,
    RateLimitError,
    SadaSendError,
    verify_webhook,
    parse_webhook,
)

API_KEY = os.environ.get("SADASEND_API_KEY")
if not API_KEY:
    sys.exit("Error: SADASEND_API_KEY environment variable is required.")
BASE_URL = os.environ.get("SADASEND_BASE_URL", "http://localhost:3000")
TEST_RECIPIENT = os.environ.get("TEST_RECIPIENT", "recipient@example.com")

# ---------------------------------------------------------------------------
# 1. Client Initialization
# ---------------------------------------------------------------------------
sadasend = SadaSend(
    api_key=API_KEY,
    base_url=BASE_URL,
    timeout=15.0,
    retry=RetryPolicy(
        max_retries=3,
        base_delay_ms=500,
        max_delay_ms=8_000,
        max_retry_after_ms=60_000,
    ),
)

print("=== SadaSend Python SDK: Full Features Demo ===\n")

# ---------------------------------------------------------------------------
# 2. Account Health, Quotas & Reputation
# ---------------------------------------------------------------------------
print("--- 1. Account Telemetry & Deliverability Health ---")
try:
    account = sadasend.account.get()
    print(f"Org: {account.get('org')} | Plan: {str(account.get('plan')).upper()}")
    print(f"Emails Quota: {account.get('emailsUsed')} / {account.get('emailQuota')}")
    print(f"Reputation Status: {account.get('reputationLevel', 'optimal')}")

    stats = sadasend.account.stats(window="14d")
    sent_count = stats.get("sent", 0)
    deliv_rate = stats.get("deliveryRate", 1.0)
    bounce_rate = stats.get("bounceRate", 0.0)
    deliv_pct = f"{deliv_rate * 100:.1f}%" if sent_count > 0 else "100.0%"
    bounce_pct = f"{bounce_rate * 100:.2f}%" if sent_count > 0 else "0.00%"
    print(f"14-Day Delivery Rate: {deliv_pct} | Bounce Rate: {bounce_pct}")

    volume = sadasend.account.volume(window="7d")
    print(f"Volume records returned: {len(volume.get('days', []))} days")
except SadaSendError as err:
    print(f"Account query failed: {err}")

# ---------------------------------------------------------------------------
# 3. Domain Management & DNS Verification
# ---------------------------------------------------------------------------
print("\n--- 2. Sending Domains & DNS Records ---")
primary_domain_id = ""
try:
    domains_resp = sadasend.domains.list()
    domains_list = domains_resp.get("domains", [])
    if domains_list:
        primary = domains_list[0]
        primary_domain_id = primary["id"]
        print(f"Primary Domain: {primary.get('name')} ({primary.get('status')})")

        # Fetch DNS records required for DKIM, SPF, and Return-Path
        records_resp = sadasend.domains.records(primary["id"])
        records = records_resp.get("records", [])
        print(f"DNS Records for verification ({len(records)} records):")
        for rec in records:
            host = rec.get("host", "")
            rec_type = rec.get("type", "")
            val_snippet = rec.get("value", "")[:32]
            verdict = rec.get("verdict", "pending")
            print(f"  [{rec_type}] {host} -> {val_snippet}... (verdict: {verdict})")

        # Trigger on-demand DNS verification check
        verify_resp = sadasend.domains.verify(primary["id"])
        print(f"DNS Verification check completed: status = {verify_resp.get('status')}")
except SadaSendError as err:
    print(f"Domain operations error: {err}")

# ---------------------------------------------------------------------------
# 4. Preflight Dry Run Send (Zero Risk)
# ---------------------------------------------------------------------------
print("\n--- 3. Preflight Dry Run (Validation Only) ---")
try:
    dry_run = sadasend.emails.send(
        from_="noreply@onboarding.sadasend.com",
        to=TEST_RECIPIENT,
        subject="Python Dry Run Preflight Check",
        html="<p>Testing guardrails without sending real email.</p>",
        dry_run=True,  # Evaluates allowlists, suppressions, and quota without dispatching
    )
    print(f"Preflight passed! dryRun = {dry_run.get('dryRun')}, messageId = {dry_run.get('id')}")
except SadaSendError as err:
    print(f"Preflight failed: {err}")

# ---------------------------------------------------------------------------
# 5. Full-Powered Transactional Send (Attachments, Tags, Custom Headers)
# ---------------------------------------------------------------------------
print("\n--- 4. Full-Featured Transactional Email Send ---")
invoice_pdf_base64 = base64.b64encode(b"%PDF-1.4 Mock Invoice Content").decode("utf-8")
sent_message_id = ""

try:
    send_resp = sadasend.emails.send(
        from_="noreply@onboarding.sadasend.com",
        to=TEST_RECIPIENT,
        reply_to="support@sadasend.com",
        subject="Invoice #1042 Available for Download",
        html="""
        <div style="font-family: sans-serif; max-width: 600px; margin: auto;">
          <h2>Your Invoice is Ready</h2>
          <p>Thank you for your business. Your receipt and invoice are attached below.</p>
          <a href="https://sadasend.com" style="background: #000; color: #fff; padding: 10px 18px; text-decoration: none; border-radius: 6px;">View Dashboard</a>
        </div>
        """,
        text="Your Invoice is Ready. Thank you for your business.",
        tags=["billing", "invoices", "python-sdk"],
        headers={
            "X-Entity-Ref-ID": "invoice-1042-python",
        },
        attachments=[
            {
                "filename": "invoice-1042.pdf",
                "content": invoice_pdf_base64,
                "contentType": "application/pdf",
            }
        ],
        # Domain-specific idempotency key: guarantees exactly-once delivery across retries and restarts
        idempotency_key=f"invoice-1042-py-{int(time.time())}",
    )
    sent_message_id = send_resp["id"]
    print(f"Email accepted! ID: {send_resp['id']} (status: {send_resp.get('status')})")
except DomainNotVerifiedError as err:
    print(f"Domain not verified! Missing DNS records: {err.records}")
except RecipientSuppressedError as err:
    print(f"Recipient is suppressed! Reason: {err.reason}")
except RecipientNotAllowlistedError as err:
    print(f"Key is in approval mode. Allowlist: {err.allowlist}")
except RateLimitError as err:
    print(f"Rate limited! Retry after {err.retry_after_seconds}s")
except SadaSendError as err:
    print(f"Send refused: [{err.code}] {err}")

# ---------------------------------------------------------------------------
# 6. Inspecting Message & Event Trail
# ---------------------------------------------------------------------------
if sent_message_id:
    print("\n--- 5. Message Event Trail Inspection ---")
    try:
        msg = sadasend.emails.get(sent_message_id)
        print(f"Message ID: {msg.get('id')}")
        recipients = ", ".join(msg.get("to", []))
        print(f"From: {msg.get('from')} -> To: {recipients}")
        print(f"Current Status: {msg.get('status')} at {msg.get('at')}")
    except SadaSendError as err:
        print(f"Fetch message failed: {err}")

    # -----------------------------------------------------------------------
    # 7. Message Resending
    # -----------------------------------------------------------------------
    print("\n--- 6. Resending Message ---")
    try:
        resend_resp = sadasend.emails.resend(sent_message_id)
        print(f"Resend queued under original key! New ID: {resend_resp.get('id')} (status: {resend_resp.get('status')})")
    except SadaSendError as err:
        print(f"Resend failed: {err}")

# ---------------------------------------------------------------------------
# 8. Scheduled Sending & Atomic Cancellation
# ---------------------------------------------------------------------------
print("\n--- 7. Scheduled Sending & Atomic Cancellation ---")
try:
    in_two_hours = (
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
    ).isoformat()

    sched_send = sadasend.emails.send(
        from_="noreply@onboarding.sadasend.com",
        to=TEST_RECIPIENT,
        subject="Python Scheduled Reminder",
        text="This email was scheduled in advance.",
        scheduled_at=in_two_hours,
    )
    print(f"Email scheduled! ID: {sched_send['id']}")

    # Cancel the scheduled email atomically before the worker picks it up
    cancel_resp = sadasend.emails.cancel(sched_send["id"])
    print(f"Email successfully cancelled! Status: {cancel_resp.get('status')}")
except SadaSendError as err:
    print(f"Scheduled send/cancel failed: {err}")

# ---------------------------------------------------------------------------
# 9. Batch Sending (Multi-Status RFC 4918 / 207)
# ---------------------------------------------------------------------------
print("\n--- 8. High-Efficiency Batch Sending ---")
try:
    batch_resp = sadasend.emails.batch(
        emails=[
            {
                "from": "noreply@onboarding.sadasend.com",
                "to": "customer1@example.com",
                "subject": "Monthly Digest: Part 1",
                "text": "Hello customer 1 from Python batch",
            },
            {
                "from": "noreply@onboarding.sadasend.com",
                "to": "customer2@example.com",
                "subject": "Monthly Digest: Part 2",
                "text": "Hello customer 2 from Python batch",
            },
        ]
    )
    accepted = batch_resp.get("accepted", 0)
    refused = batch_resp.get("refused", 0)
    total = batch_resp.get("total", 0)
    print(f"Batch processed: {accepted} accepted, {refused} refused out of {total}")
    for item in batch_resp.get("results", []):
        idx = item.get("index")
        ok_status = item.get("ok")
        result_desc = item.get("status") or item.get("error")
        print(f"  Item #{idx}: ok = {ok_status}, status = {result_desc}")
except SadaSendError as err:
    print(f"Batch send failed: {err}")

# ---------------------------------------------------------------------------
# 10. Server-Side Liquid Template Rendering
# ---------------------------------------------------------------------------
print("\n--- 9. Server-Side Template Rendering ---")
try:
    templates_resp = sadasend.templates.list()
    templates = templates_resp.get("templates", [])
    if templates:
        tpl = templates[0]
        print(f"Using template: {tpl.get('name')} (v{tpl.get('version')})")

        rendered = sadasend.templates.render(
            tpl["id"],
            variables={
                "customer_name": "Jordan Lee",
                "order_id": "ORD-PY-5544",
                "total": "$249.99",
            },
        )
        print(f"Rendered Subject: {rendered.get('subject')}")
        snippet = rendered.get("html", "")[:80]
        print(f"Rendered HTML snippet: {snippet}...")
except SadaSendError as err:
    print(f"Template rendering failed: {err}")

# ---------------------------------------------------------------------------
# 11. Suppression List Management
# ---------------------------------------------------------------------------
print("\n--- 10. Suppression Management ---")
try:
    unsub_addr = f"unsubscribed-py-{int(time.time())}@example.com"
    add_supp = sadasend.suppressions.add(address=unsub_addr, reason="unsubscribe")
    already = add_supp.get("already", False)
    print(f"Suppressed address: {add_supp.get('address')} (already = {already})")

    list_supp = sadasend.suppressions.list(limit=5)
    print(f"Total suppressions on account: {list_supp.get('total', 0)}")
except SadaSendError as err:
    print(f"Suppression management failed: {err}")

# ---------------------------------------------------------------------------
# 12. Constant-Time Webhook Signature Verification
# ---------------------------------------------------------------------------
print("\n--- 11. Secure Webhook Verification ---")
webhook_secret = "whsec_sample_webhook_secret_key_py_998877"
webhook_payload = json.dumps({
    "id": "evt_sample_deliver_py_01",
    "type": "email.delivered",
    "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "data": {
        "messageId": "msg_sample_py_123",
        "recipient": TEST_RECIPIENT,
    },
})

# Constructing header format `t=<unix-seconds>,v1=<hex>`
timestamp_sec = int(time.time())
sig_hex = hmac.new(
    webhook_secret.encode("utf-8"),
    f"{timestamp_sec}.{webhook_payload}".encode("utf-8"),
    hashlib.sha256,
).hexdigest()
signature_header = f"t={timestamp_sec},v1={sig_hex}"

# In your webhook handler (Flask / FastAPI / Django):
is_valid = verify_webhook(webhook_secret, webhook_payload, signature_header)
print(f"Webhook signature validity: {'VERIFIED (valid)' if is_valid else 'REJECTED (invalid)'}")

event = parse_webhook(webhook_secret, webhook_payload, signature_header)
if event:
    print(f"Parsed Webhook Event: type = {event.get('type')}, id = {event.get('id')}")

print("\n=== SadaSend Python SDK Demo Completed Successfully ===\n")

