#!/usr/bin/env python3
import base64
import datetime
import hashlib
import hmac
import json
import os
import sys
import time
from pathlib import Path

# Add sadasend package to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sadasend import SadaSend, verify_webhook, parse_webhook

BASE_URL = os.environ.get("SADASEND_BASE_URL", "http://localhost:3000")
API_KEY = os.environ.get("SADASEND_API_KEY")
if not API_KEY:
    sys.exit("Error: SADASEND_API_KEY environment variable is required.")
TEST_RECIPIENT = os.environ.get("TEST_RECIPIENT", "recipient@example.com")

print("\n======================================================")
print("SadaSend Python SDK Live End-to-End Verification")
print(f"Target Base URL: {BASE_URL}")
print("API Key:         [configured]")
print("======================================================\n")

client = SadaSend(API_KEY, base_url=BASE_URL)

passed = 0
failed = 0


def check(name, fn):
    global passed, failed
    sys.stdout.write(f"• Testing [{name}] ... ")
    sys.stdout.flush()
    try:
        fn()
        print("\033[32mPASS\033[0m")
        passed += 1
    except Exception as err:
        print(f"\033[31mFAIL\033[0m: {err}")
        if hasattr(err, "body"):
            print(f"   Response Body: {json.dumps(getattr(err, 'body'))}")
        failed += 1


# 1. Account Operations
domain_id = ""
template_id = ""
sent_message_id = ""


def test_account_get():
    res = client.account.get()
    if not res.get("org") or not res.get("plan"):
        raise ValueError("Missing org or plan in account info")


check("account.get()", test_account_get)


def test_account_stats():
    res = client.account.stats(window="14d")
    if "sent" not in res:
        raise ValueError("Missing sent count in account stats")


check("account.stats()", test_account_stats)


def test_account_volume():
    res = client.account.volume(window="7d")
    if not isinstance(res.get("days"), list):
        raise ValueError("Missing days array in account volume")


check("account.volume()", test_account_volume)


def test_account_checklist():
    res = client.account.checklist()
    if not isinstance(res.get("items"), list):
        raise ValueError("Missing items in account checklist")


check("account.checklist()", test_account_checklist)


# 2. Domain Operations
def test_domains_list():
    global domain_id
    res = client.domains.list()
    if not isinstance(res.get("domains"), list):
        raise ValueError("Missing domains array")
    if res["domains"]:
        domain_id = res["domains"][0]["id"]


check("domains.list()", test_domains_list)

if domain_id:

    def test_domains_records():
        res = client.domains.records(domain_id)
        if not isinstance(res.get("records"), list):
            raise ValueError("Missing records array")

    check("domains.records()", test_domains_records)

    def test_domains_verify():
        res = client.domains.verify(domain_id)
        if not res.get("status"):
            raise ValueError("Missing status in verify response")

    check("domains.verify()", test_domains_verify)


# 3. Email Operations
def test_emails_send():
    global sent_message_id
    res = client.emails.send(
        from_="noreply@onboarding.sadasend.com",
        to=TEST_RECIPIENT,
        subject="Python SDK Live E2E Test",
        html="<p>Live test from updated Python SDK with full feature set.</p>",
        tags=["python-sdk", "live-test"],
        attachments=[
            {
                "filename": "python_report.txt",
                "content": base64.b64encode(b"Python live test content").decode("utf-8"),
                "contentType": "text/plain",
            }
        ],
    )
    if not res.get("id") or res.get("status") != "queued":
        raise ValueError(f"Unexpected send status: {res.get('status')}")
    sent_message_id = res["id"]


check("emails.send() with attachment and tags", test_emails_send)

if sent_message_id:

    def test_emails_get():
        res = client.emails.get(sent_message_id)
        if res.get("id") != sent_message_id:
            raise ValueError(f"Message id mismatch: {res.get('id')}")
        if not isinstance(res.get("to"), list):
            raise ValueError("to field must be a list")

    check("emails.get()", test_emails_get)

    def test_emails_resend():
        res = client.emails.resend(sent_message_id)
        if not res.get("id") or res.get("status") != "queued":
            raise ValueError(f"Unexpected resend status: {res.get('status')}")

    check("emails.resend()", test_emails_resend)


def test_emails_list():
    res = client.emails.list(limit=5)
    if not isinstance(res.get("messages"), list):
        raise ValueError("Missing messages list")


check("emails.list()", test_emails_list)


def test_emails_batch():
    res = client.emails.batch(
        emails=[
            {
                "from": "noreply@onboarding.sadasend.com",
                "to": TEST_RECIPIENT,
                "subject": "Python Batch 1",
                "text": "Batch item 1 content from Python",
            },
            {
                "from": "noreply@onboarding.sadasend.com",
                "to": TEST_RECIPIENT,
                "subject": "Python Batch 2",
                "text": "Batch item 2 content from Python",
            },
        ]
    )
    if res.get("total") != 2 or len(res.get("results", [])) != 2:
        raise ValueError(f"Unexpected batch result count: {res.get('total')}")


check("emails.batch()", test_emails_batch)


def test_emails_cancel():
    future_time = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)).isoformat()
    send_res = client.emails.send(
        from_="noreply@onboarding.sadasend.com",
        to=TEST_RECIPIENT,
        subject="Python Cancel Test",
        text="To be cancelled",
        scheduled_at=future_time,
    )
    sched_id = send_res["id"]
    cancel_res = client.emails.cancel(sched_id)
    if cancel_res.get("status") != "cancelled":
        raise ValueError(f"Expected cancelled status, got: {cancel_res.get('status')}")


check("emails.cancel() on scheduled email", test_emails_cancel)


# 4. Template Operations
def test_templates_list():
    global template_id
    res = client.templates.list()
    if not isinstance(res.get("templates"), list):
        raise ValueError("Missing templates list")
    if res["templates"]:
        template_id = res["templates"][0]["id"]


check("templates.list()", test_templates_list)

if template_id:

    def test_templates_get():
        res = client.templates.get(template_id)
        if res.get("id") != template_id:
            raise ValueError(f"Template ID mismatch: {res.get('id')}")

    check("templates.get()", test_templates_get)

    def test_templates_render():
        client.templates.render(
            template_id,
            variables={"customer_name": "Python User", "order_id": "py_9876", "total": "$149.00"},
        )

    check("templates.render()", test_templates_render)


# 5. Suppression Operations
test_suppress_addr = f"py-live-suppress-{int(time.time())}@example.com"


def test_suppressions_add():
    res = client.suppressions.add(address=test_suppress_addr, reason="manual")
    if res.get("address") != test_suppress_addr:
        raise ValueError(f"Expected address {test_suppress_addr}, got: {res.get('address')}")


check("suppressions.add()", test_suppressions_add)


def test_suppressions_list():
    res = client.suppressions.list(q=test_suppress_addr)
    if not isinstance(res.get("suppressions"), list):
        raise ValueError("Missing suppressions list")
    found = any(s.get("address") == test_suppress_addr for s in res["suppressions"])
    if not found:
        raise ValueError("Added suppression address not found in list query")


check("suppressions.list()", test_suppressions_list)


# 6. Webhook Operations
def test_webhooks_list():
    res = client.webhooks.list()
    if not isinstance(res.get("webhooks"), list):
        raise ValueError("Missing webhooks list")
    if res["webhooks"]:
        wid = res["webhooks"][0]["id"]
        deliv = client.webhooks.deliveries(wid, limit=5)
        if not isinstance(deliv.get("deliveries"), list):
            raise ValueError("Missing deliveries list")


check("webhooks.list()", test_webhooks_list)


def test_webhooks_verify():
    secret = "whsec_test_secret_for_live_verification_py_123"
    payload = json.dumps({
        "id": "evt_py_123",
        "type": "message.delivered",
        "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "data": {"id": "msg_py_123"},
    })
    t = int(time.time())
    sig = hmac.new(secret.encode("utf-8"), f"{t}.{payload}".encode("utf-8"), hashlib.sha256).hexdigest()
    header = f"t={t},v1={sig}"

    is_valid = verify_webhook(secret, payload, header)
    if not is_valid:
        raise ValueError("Expected valid HMAC signature to verify successfully")

    parsed = parse_webhook(secret, payload, header)
    if not parsed or parsed.get("id") != "evt_py_123":
        raise ValueError("parse_webhook failed to return expected event dict")

    tampered = verify_webhook(secret, payload + "!", header)
    if tampered:
        raise ValueError("Tampered payload should have failed signature verification")


check("webhooks.verify_webhook() HMAC cryptographic signature verification", test_webhooks_verify)

print("\n------------------------------------------------------")
print(f"Results: \033[32m{passed} PASSED\033[0m | \033[31m{failed} FAILED\033[0m out of {passed + failed} checks")
print("------------------------------------------------------\n")

if failed > 0:
    sys.exit(1)
else:
    print("\033[32mAll Python SDK operations verified and 100% operational!\033[0m\n")
    sys.exit(0)

