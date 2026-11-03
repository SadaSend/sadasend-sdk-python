# Changelog

All notable changes to the `sadasend` Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2026-10-30

### Added
- **Convenience Resource Nesting Aliases**:
  - Added nested client aliases matching TypeScript SDK ergonomics: `client.inbound.routes`, `client.inbound.messages`, `client.dmarc.reports`, `client.dmarc.summary`, `client.arbiter.cooldowns`, `client.arbiter.tickets`, `client.inboxes.create`, `client.testing.inboxes`, `client.testing.waitForCode`.
- **Inbound MX Routing & Webhook Ingestion Engine (`client.inbound`)**:
  - `client.inbound_routes`: `list()`, `create()`, `get()`, `update()`, `delete()`.
  - `client.inbound_messages`: `list()`, `get()`.
  - `client.inbound.parse()`: Context-safe parser stripping signatures/history (~85% token reduction) and calculating prompt injection risk score.
  - `client.inbound.simulate()`: Tests routing rules against incoming recipient addresses.
- **DMARC Deliverability Radar & Forensic Reporting (`client.dmarc`)**:
  - `client.dmarc_reports`: `list()`, `create()`, `get()`.
  - `client.dmarc_domains.summary(domain=...)`: Deliverability scorecard and policy upgrade recommendations.
  - `client.dmarc.threats()`: Unauthorized spoofing sources and forensic threat analysis.
- **Multi-Agent Collision Arbiter & Cooldowns (`client.arbiter`)**:
  - `client.arbiter.stats()`: Real-time collision metrics and active cooldown count.
  - `client.arbiter_recipients`: `set_cooldown()`, `clear_cooldown()`, `status()`.
  - `client.arbiter_tickets`: `create()`, `delete()`.
- **Multi-Agent Ephemeral Inboxes (`client.inboxes`)**:
  - `client.inboxes.ephemeral()`: Dynamic temporary inboxes with automatic TTL expiration.
  - `client.inboxes.otp()`: Reactive long-polling extraction of 2FA codes without busy-wait loops.
  - `client.inboxes.messages()`, `client.inboxes.stream()`, `client.inboxes.inbound()`.
- **E2E Testing Sandbox (`client.testing`)**:
  - `client.testing.inbound()`, `client.testing.wait_for_code()`, `client.testing_inboxes.code()`, `client.testing_inboxes.latest()`.
- **Message Provenance & Hold Types**:
  - Added `provenance` dictionary support to `client.emails.send(...)` (`channel`, `source`, `agent_name`, `priority`).
  - Stamped `x-sadasend-priority` headers on critical dispatches.
- **Slack Integration**:
  - Added `client.integrations.slack()` status inspection.

### Removed
- Removed billing client operations (`client.billing`) to maintain strict perimeter alignment with the backend API key auth boundary (Paddle checkout, subscription management, and credit packs require browser session authentication and are managed in the dashboard).

## [0.1.1] - 2026-10-24

### Added
- **Deliverability Shield & Verification**:
  - Added `verify_before_send` parameter to `client.emails.send(...)` and `client.emails.batch(...)` for real-time MX/syntax/disposable verification before queuing.
  - Added `client.tools.verify(email=...)` and `client.tools.verify_batch(emails=[...])` methods (with `verifyBatch` camelCase alias).
- **RFC 8058 One-Click Header**:
  - Added `marketing` parameter to `client.emails.send(...)` and `client.emails.batch(...)` to automatically inject `List-Unsubscribe` and `List-Unsubscribe-Post` headers.
- **Prepaid Credit Packs & Paddle Checkout**:
  - Added `client.billing.credits_checkout(pack=..., type=..., return_url=...)` method for Paddle credit packs checkout initialization.
- **Typed Guardrail Exception Classes**:
  - Added dedicated typed exception subclasses: `UndeliverableRecipientError`, `InvalidSubjectError`, `InvalidDateError`, `BatchSizeExceededError`, `PlanTierInsufficientError`, `AnonymousLimitExceededError`, `InvitationAlreadyPendingError`, and `InvalidPlanError`.
- **UTM Campaign Tracking & Parameter Normalization**:
  - Added native `utm` dictionary support to `client.emails.send(...)` (`source`, `medium`, `campaign`, `term`, `content`, `override_existing`).
  - Added `client.tools.utm(...)` and `client.tools.build_utm(...)` methods (`POST /tools/utm`) to normalize, validate, and inject campaign parameters into target URLs.
- **Convenience Aliases & Parity with TypeScript SDK**:
  - Added `client.keys.approvals()` pointing to `client.keys_approvals.list()`.
  - Added `client.support.tickets()` and `client.support.ticket(id)`.

## [0.1.0] - 2026-10-10

### Added
- **Zero-Dependency Architecture**: Built entirely on Python standard library modules (`urllib.request`, `hmac`, `hashlib`, `json`). Zero runtime wheels, zero supply-chain CVE vulnerabilities.
- **Client Transport & Autonomous Agent Guardrails**:
  - `SadaSend` client with per-attempt timeout and structured exception propagation.
  - Automatic `Idempotency-Key` generation on mutating calls (`POST`, `PATCH`, `PUT`) with guaranteed key reuse across transient retries.
  - Server-enforced rate limiting and exponential backoff with full jitter.
  - Strict compliance with `Retry-After` HTTP headers (numeric seconds and RFC 9110 HTTP-dates), without artificial exponential backoff inflation.
  - Automatic suppression and non-retryability of guardrail refusals (`RecipientNotAllowlistedError`, `RecipientSuppressedError`, `DomainNotVerifiedError`, `InsufficientScopeError`).
- **Complete Resource Operations**:
  - `account`: get, stats, volume sparklines, checklist, circuit breakers, staff access audit.
  - `domains`: list, DNS records inspection, on-demand verification.
  - `emails`: send (transactional with cc, bcc, reply-to, attachments, tags, liquid variables, dry-run, scheduled dispatch), get, list, cancel, resend, and batch (207 Multi-Status).
  - `keys`: list keys and approval queues.
  - `suppressions`: list suppressed addresses and add manual suppressions.
  - `templates`: list, get, test render, and preview dispatch.
  - `tools`: deliverability tools catalog and free diagnostic checks.
  - `webhooks`: endpoints list and delivery logs inspection.
- **Cryptographic HMAC-SHA256 Webhook Verification**:
  - `verify_webhook` and `parse_webhook` with constant-time digest comparison (`hmac.compare_digest`).
  - Native support for both `str` and raw `bytes` request payloads (FastAPI, Flask, Django, Starlette).
  - Replay-attack prevention with timestamp tolerance verification (`sadasend-signature` header).
- **Type Safety & IDE Support**:
  - PEP 561 `py.typed` marker package.
  - Full type annotations for `SadaSend` resource attributes and method signatures.
- **Exhaustive Test Suite**:
  - Comprehensive unit test coverage across client transport, retries, error hierarchy, webhooks, resources, provenance, and packaging.
