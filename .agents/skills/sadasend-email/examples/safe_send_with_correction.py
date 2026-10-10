#!/usr/bin/env python3
"""
Autonomous AI Agent Execution Pattern — SadaSend Python SDK

Demonstrates:
  1. Client attribution & provenance configuration
  2. Preflight dry run (zero cost, zero deliverability risk)
  3. Guardrail interception & autonomous self-correction
  4. Handling Human Approval Queue ('pending_approval')
  5. Live send with deterministic idempotency
"""

import datetime
import os
import sys
from typing import Any, Dict

from sadasend import (
    DomainNotVerifiedError,
    RateLimitError,
    RecipientNotAllowlistedError,
    RecipientSuppressedError,
    RetryPolicy,
    SadaSend,
    SadaSendError,
)


def agent_email_workflow(target_recipient: str) -> Dict[str, Any]:
    api_key = os.environ.get("SADASEND_API_KEY")
    if not api_key:
        raise ValueError("SADASEND_API_KEY environment variable is required")

    # 1. Initialize client with full persona attribution
    client = SadaSend(
        api_key=api_key,
        default_agent_name="customer-onboarding-agent",
        default_source="agent",
        default_channel="sdk",
        timeout=15.0,
        retry=RetryPolicy(max_retries=3),
    )

    print(f"🤖 Agent analyzing email dispatch to: {target_recipient}...")

    # 2. Step 1: Preflight Dry Run (Checks deliverability & guardrails without sending)
    try:
        preflight = client.emails.send(
            from_="welcome@onboarding.sadasend.com",
            to=target_recipient,
            subject="Welcome to our platform",
            text="Your account is now ready.",
            dry_run=True,
        )
        print("✅ Preflight deliverability checks passed:", preflight.get("status"))
    except RecipientNotAllowlistedError as err:
        print("⚠️ Blocked by Agent Allowlist Guardrail!")
        print(f"Target '{err.recipient}' is outside authorized patterns: {err.allowlist}")
        return {
            "status": "refused",
            "reason": "outside_allowlist",
            "authorized_patterns": err.allowlist,
        }
    except RecipientSuppressedError as err:
        print(f"⚠️ Target recipient is suppressed (reason: {err.reason}). Aborting send.")
        return {
            "status": "refused",
            "reason": "suppressed",
            "suppression_reason": err.reason,
        }
    except DomainNotVerifiedError as err:
        print(f"❌ Sending domain is not verified! DNS records required: {err.records}")
        return {
            "status": "refused",
            "reason": "domain_unverified",
            "records": err.records,
        }
    except SadaSendError as err:
        print(f"❌ Preflight failed: [{err.code}] {err.message}")
        return {"status": "failed", "error": err.message}

    # 3. Step 2: Live Dispatch with Guaranteed Idempotency
    today_str = datetime.date.today().isoformat()
    idempotency_key = f"onboarding-{target_recipient}-{today_str}"

    try:
        send_resp = client.emails.send(
            from_="welcome@onboarding.sadasend.com",
            to=target_recipient,
            subject="Welcome to our platform",
            html="<h1>Welcome!</h1><p>Your account is ready.</p>",
            text="Welcome! Your account is ready.",
            tags=["onboarding", "agent-dispatched"],
            idempotency_key=idempotency_key,
        )
    except RateLimitError as err:
        print(f"⏳ Rate limited. Must wait {err.retry_after_seconds}s before retrying.")
        return {"status": "rate_limited", "retry_after": err.retry_after_seconds}
    except SadaSendError as err:
        print(f"❌ Dispatch failed: [{err.code}] {err.message}")
        return {"status": "failed", "error": err.message}

    # 4. Step 3: Handle Normal Send vs Human Approval Queue
    if send_resp.get("status") == "pending_approval":
        print(f"🛡️ Message queued for HUMAN APPROVAL (ID: {send_resp['id']}).")
        return {"status": "held_for_approval", "message_id": send_resp["id"]}

    print(f"🚀 Message queued for delivery (ID: {send_resp['id']}).")
    return {"status": "dispatched", "message_id": send_resp["id"]}


if __name__ == "__main__":
    recipient = sys.argv[1] if len(sys.argv) > 1 else "demo@example.com"
    result = agent_email_workflow(recipient)
    print("Workflow outcome:", result)
