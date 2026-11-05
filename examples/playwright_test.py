"""
Playwright & Pytest E2E Test Example with SadaSend Ephemeral Inboxes.

Demonstrates modern, zero-polling reactive testing (<150ms) replacing
Mailosaur and Mailtrap in Python.

Run with pytest and pytest-playwright:
    pytest examples/playwright_test.py
"""

from __future__ import annotations

import os
import pytest

# Fixtures ephemeral_inbox and create_inbox are auto-registered via pytest11 entrypoint.
# You can also import explicitly:
# from sadasend.playwright import ephemeral_inbox, create_inbox, EphemeralInboxFixture


@pytest.mark.skipif(not os.environ.get("SADASEND_API_KEY"), reason="Requires SADASEND_API_KEY")
def test_user_signup_with_2fa_otp(ephemeral_inbox):
    """Demonstrates real-time OTP capture (<150ms) with automated teardown."""
    # 1. Provide disposable address to web form
    signup_email = ephemeral_inbox.email
    assert "@" in signup_email

    # 2. In real browser tests with page fixture (pytest-playwright):
    #    page.goto("https://app.example.com/signup")
    #    page.fill("#email", signup_email)
    #    page.click("#submit")

    # 3. Wait for real-time 6-digit OTP code push
    #    otp = ephemeral_inbox.wait_for_otp(timeout_ms=15_000)
    #    page.fill("#otp", otp)
    #    assert page.is_visible("#dashboard")

    # 4. Or extract magic sign-in links:
    #    link = ephemeral_inbox.wait_for_magic_link()
    #    page.goto(link)


def test_ephemeral_inbox_structure():
    """Validates EphemeralInboxFixture structure and methods."""
    from sadasend import SadaSend, EphemeralInboxFixture

    client = SadaSend(api_key="sada_mock_sk_test")
    fixture = EphemeralInboxFixture(
        client,
        {
            "id": "inb_demo_1",
            "email": "demo@sada.email",
            "alias": "demo",
            "domain": "sada.email",
        },
    )

    assert fixture.id == "inb_demo_1"
    assert fixture.email == "demo@sada.email"
    assert hasattr(fixture, "wait_for_otp")
    assert hasattr(fixture, "wait_for_code")
    assert hasattr(fixture, "wait_for_magic_link")
    assert hasattr(fixture, "wait_for_message")
    assert hasattr(fixture, "get_messages")
    # camelCase aliases
    assert hasattr(fixture, "waitForOtp")
    assert hasattr(fixture, "waitForCode")

