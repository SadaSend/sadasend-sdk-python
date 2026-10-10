# Changelog

All notable changes to the `sadasend` Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
