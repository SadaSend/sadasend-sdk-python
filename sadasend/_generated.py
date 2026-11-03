"""
Generated from openapi.json. DO NOT EDIT.

Run `bun run sdk:python` to regenerate. CI runs `bun run sdk:python:check`, which
regenerates and fails on any difference — so a route added in the morning is in this
file before that morning's pull request can land.

Only the operations live here. The transport, retries, error classes and webhook
verifier are hand-written in _client.py, errors.py and webhooks.py — a generator cannot
write "obey Retry-After" or "never retry a guardrail refusal", and those are the whole
point of the client.

Operations reachable with an API key: 66. Cookie-session-only operations excluded: 58 —
the dashboard's own surface, where a method here would return 401 on every call.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

if TYPE_CHECKING:  # pragma: no cover
    from ._client import SadaSend

SPEC_VERSION = "1.0.0"


class Account:
    """`client.account` — 6 operations."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def checklist(self) -> Dict[str, Any]:
        """
        Onboarding completion, derived from real rows
        """
        return self._client._request("GET", "/account/checklist")

    def circuit_breakers(self) -> Dict[str, Any]:
        """
        Active AI agent velocity circuit breakers

        Lists currently tripped velocity circuit breakers for autonomous AI agents.
        """
        return self._client._request("GET", "/account/circuit-breakers")

    def get(self) -> Dict[str, Any]:
        """
        Plan, state, quotas and usage

        Every constraint trigger in the dashboard reads from this object.
        """
        return self._client._request("GET", "/account")

    def staff_access(self, limit: Optional[Any] = None) -> Dict[str, Any]:
        """
        Every message body a member of our staff has opened

        Who, when and under what reason. Only body reads appear here — delivery events
        and metadata are excluded, because listing them would drown the signal that
        matters.

        Args:
            limit: query parameter.
        """
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        return self._client._request("GET", "/account/staff-access", params=params)

    def stats(self, window: Optional[Any] = None, by_tag: Optional[Any] = None, bounces: Optional[Any] = None, engagement: Optional[Any] = None, provenance: Optional[Any] = None, by_channel: Optional[Any] = None, by_source: Optional[Any] = None, top_agents: Optional[Any] = None) -> Dict[str, Any]:
        """
        Sent, delivered and the rates, over a window

        Args:
            window: query parameter.
            by_tag: query parameter.
            bounces: query parameter.
            engagement: query parameter.
            provenance: query parameter.
            by_channel: query parameter.
            by_source: query parameter.
            top_agents: query parameter.
        """
        params: Dict[str, Any] = {}
        if window is not None:
            params["window"] = window
        if by_tag is not None:
            params["by_tag"] = by_tag
        if bounces is not None:
            params["bounces"] = bounces
        if engagement is not None:
            params["engagement"] = engagement
        if provenance is not None:
            params["provenance"] = provenance
        if by_channel is not None:
            params["by_channel"] = by_channel
        if by_source is not None:
            params["by_source"] = by_source
        if top_agents is not None:
            params["top_agents"] = top_agents
        return self._client._request("GET", "/account/stats", params=params)

    def volume(self, window: Optional[Any] = None) -> Dict[str, Any]:
        """
        Daily counts for the sparkline

        Zero-fills empty days, so a sparkline cannot read silence as steady traffic.

        Args:
            window: query parameter.
        """
        params: Dict[str, Any] = {}
        if window is not None:
            params["window"] = window
        return self._client._request("GET", "/account/volume", params=params)


class Arbiter:
    """`client.arbiter` — 1 operation."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def stats(self) -> Dict[str, Any]:
        """
        Get account-level collision arbitration statistics

        Returns real-time collision statistics including total collisions prevented,
        active contact cooldowns, and open support ticket holds.
        """
        return self._client._request("GET", "/arbiter/stats")


class ArbiterRecipients:
    """`client.arbiter_recipients` — 3 operations."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def clear_cooldown(self, recipient: str) -> Dict[str, Any]:
        """
        Clear contact cooldown for a recipient

        Immediately removes active cross-agent cooldown on a recipient, allowing
        outbound agent communication to resume.

        Args:
            recipient: path segment.
        """
        return self._client._request("DELETE", f"/arbiter/recipients/{recipient}/cooldown")

    def set_cooldown(self, recipient: str, duration: Optional[str] = None, cooldown_seconds: Optional[int] = None, priority: Optional[str] = None, agent_name: Optional[str] = None, idempotency_key: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
        """
        Set or extend contact cooldown for a recipient

        Manually places a recipient address on cross-agent contact cooldown for a
        specified duration (e.g. "24h", "12h", "1h", or seconds), suppressing subsequent
        outbound agent dispatches.

        Args:
            recipient: path segment.
            duration: Cooldown duration string (e.g. "24h", "12h", "1h", "30m", or seconds)
            cooldown_seconds: Cooldown duration in seconds
            priority: Priority level of the contact touch (auth, support, billing, follow_up, marketing)
            agent_name: Name of the agent or operator initiating the cooldown
        """
        body: Dict[str, Any] = dict(extra)
        if duration is not None:
            body["duration"] = duration
        if cooldown_seconds is not None:
            body["cooldownSeconds"] = cooldown_seconds
        if priority is not None:
            body["priority"] = priority
        if agent_name is not None:
            body["agentName"] = agent_name
        return self._client._request("POST", f"/arbiter/recipients/{recipient}/cooldown", body=body, idempotency_key=idempotency_key)

    def status(self, recipient: str) -> Dict[str, Any]:
        """
        Inspect contact cooldown, support ticket, and send velocity for recipient (Task
        6)

        Inspects whether an email recipient is currently within an active cross-agent
        contact cooldown window, has an unresolved open customer support ticket, or is
        experiencing a send velocity anomaly.

        Args:
            recipient: path segment.
        """
        return self._client._request("GET", f"/arbiter/recipients/{recipient}/status")


class ArbiterTickets:
    """`client.arbiter_tickets` — 2 operations."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def create(self, recipient: str, ticket_id: str, subject: Optional[str] = None, hold_priority_threshold: Optional[int] = None, metadata: Optional[Dict[str, Any]] = None, idempotency_key: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
        """
        Register active support ticket to hold low-priority agent outreach

        Registers an open support ticket for a customer email address. Autonomous SDR,
        follow-up, and marketing agent emails targeting this customer will automatically
        be held in the approval queue until the ticket is resolved.

        Args:
            recipient: Customer email address
            ticket_id: Unique support ticket identifier (e.g. TICK-1049, ZEN-8842)
            subject: Ticket subject or summary
            hold_priority_threshold: Priority threshold for hold (default 3: holds follow_up and marketing)
            metadata: Optional.
        """
        body: Dict[str, Any] = dict(extra)
        if recipient is not None:
            body["recipient"] = recipient
        if ticket_id is not None:
            body["ticketId"] = ticket_id
        if subject is not None:
            body["subject"] = subject
        if hold_priority_threshold is not None:
            body["holdPriorityThreshold"] = hold_priority_threshold
        if metadata is not None:
            body["metadata"] = metadata
        return self._client._request("POST", "/arbiter/tickets", body=body, idempotency_key=idempotency_key)

    def delete(self, recipient: str) -> Dict[str, Any]:
        """
        Resolve or clear support ticket hold for recipient

        Resolves or clears an active customer support ticket hold, allowing automated
        follow-up and marketing outreach to resume.

        Args:
            recipient: path segment.
        """
        return self._client._request("DELETE", f"/arbiter/tickets/{recipient}")


class Dmarc:
    """`client.dmarc` — 1 operation."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def threats(self, domain: Optional[Any] = None, limit: Optional[Any] = None, offset: Optional[Any] = None) -> Dict[str, Any]:
        """
        List detected DMARC forensic spoofing threats and unauthorized senders (Task 33)

        Lists all flagged spoofing attempts, unauthenticated external MTAs, and
        third-party sending misconfigurations targeting customer domains.

        Args:
            domain: query parameter.
            limit: query parameter.
            offset: query parameter.
        """
        params: Dict[str, Any] = {}
        if domain is not None:
            params["domain"] = domain
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        return self._client._request("GET", "/dmarc/threats", params=params)


class DmarcDomains:
    """`client.dmarc_domains` — 1 operation."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def summary(self, domain: str, days: Optional[Any] = None) -> Dict[str, Any]:
        """
        Get DMARC forensic radar deliverability scorecard and policy advice (Task 33)

        Generates real-time deliverability scorecard, compliance rates across lookback
        window, identified unauthorized sender source IPs, and actionable guidance for
        advancing policy from p=none to p=quarantine and p=reject.

        Args:
            domain: path segment.
            days: query parameter.
        """
        params: Dict[str, Any] = {}
        if days is not None:
            params["days"] = days
        return self._client._request("GET", f"/dmarc/domains/{domain}/summary", params=params)


class DmarcReports:
    """`client.dmarc_reports` — 3 operations."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def create(self, xml: Optional[str] = None, data: Optional[str] = None, content: Optional[str] = None, filename: Optional[str] = None, idempotency_key: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
        """
        Ingest RFC 7489 aggregate DMARC XML feedback report (Task 33)

        Ingests and evaluates a DMARC aggregate XML report (RUA feedback envelope) from
        mail receivers (Google, Microsoft, Yahoo, Comcast). Supports raw XML,
        JSON-wrapped base64, Gzip (.gz), and Zip (.zip) archives. Idempotently
        deduplicates reports by orgName and reportId. Requires Pro plan ($19/mo) or
        above.

        Args:
            xml: Raw or base64-encoded DMARC XML string or compressed archive
            data: Alternative payload field for base64 XML data
            content: Alternative payload field for XML content
            filename: Optional original filename (e.g. google.com!example.com!1700000000.xml.gz)
        """
        body: Dict[str, Any] = dict(extra)
        if xml is not None:
            body["xml"] = xml
        if data is not None:
            body["data"] = data
        if content is not None:
            body["content"] = content
        if filename is not None:
            body["filename"] = filename
        return self._client._request("POST", "/dmarc/reports", body=body, idempotency_key=idempotency_key)

    def get(self, id_: str) -> Dict[str, Any]:
        """
        Get DMARC aggregate report details and evaluated sending records (Task 33)

        Retrieves the complete report envelope and all evaluated sending source IP
        records, SPF/DKIM alignment results, and forensic spoofing flags.

        Args:
            id_: path segment.
        """
        return self._client._request("GET", f"/dmarc/reports/{id_}")

    def list(self, domain: Optional[Any] = None, limit: Optional[Any] = None, offset: Optional[Any] = None) -> Dict[str, Any]:
        """
        List ingested DMARC aggregate reports with pagination (Task 33)

        Lists aggregate DMARC reports ingested for customer domains with compliance
        statistics, message counts, and reporting period ranges.

        Args:
            domain: query parameter.
            limit: query parameter.
            offset: query parameter.
        """
        params: Dict[str, Any] = {}
        if domain is not None:
            params["domain"] = domain
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        return self._client._request("GET", "/dmarc/reports", params=params)


class Domains:
    """`client.domains` — 3 operations."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def list(self) -> Dict[str, Any]:
        """
        Sending domains
        """
        return self._client._request("GET", "/domains")

    def records(self, id_: str) -> Dict[str, Any]:
        """
        The DNS records to publish, with a verdict on each

        Args:
            id_: path segment.
        """
        return self._client._request("GET", f"/domains/{id_}/records")

    def verify(self, id_: str, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Re-check DNS now

        Args:
            id_: path segment.
        """
        return self._client._request("POST", f"/domains/{id_}/verify", idempotency_key=idempotency_key)


class Emails:
    """`client.emails` — 6 operations."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def batch(self, emails: List[Dict[str, Any]], idempotency_key: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
        """
        Send up to 100 emails, each independently accepted or rejected

        Answers **207 always**, even when every item succeeded — the response shape does
        not change with the outcome, so the status code should not either. Every item
        carries its own result; one suppressed address does not fail the other
        ninety-nine. An `Idempotency-Key` is applied per item as `<key>:<index>`, so
        retrying the whole batch completes exactly the items that did not get through.

        Args:
            emails: Required.
        """
        body: Dict[str, Any] = dict(extra)
        if emails is not None:
            body["emails"] = emails
        return self._client._request("POST", "/emails/batch", body=body, idempotency_key=idempotency_key)

    def cancel(self, id_: str) -> Dict[str, Any]:
        """
        Cancel a scheduled send

        Only while still queued. Claimed atomically against the worker.

        Args:
            id_: path segment.
        """
        return self._client._request("DELETE", f"/emails/{id_}")

    def get(self, id_: str) -> Dict[str, Any]:
        """
        One message, with its full event trail

        Args:
            id_: path segment.
        """
        return self._client._request("GET", f"/emails/{id_}")

    def list(self, status: Optional[Any] = None, q: Optional[Any] = None, tag: Optional[Any] = None, channel: Optional[Any] = None, source: Optional[Any] = None, agent_name: Optional[Any] = None, limit: Optional[Any] = None, cursor: Optional[Any] = None) -> Dict[str, Any]:
        """
        Recent messages, filtered

        Cursor paginated. OFFSET re-scans everything it skips and rows shift under the
        reader as new mail arrives.

        Args:
            status: query parameter.
            q: query parameter.
            tag: query parameter.
            channel: query parameter.
            source: query parameter.
            agent_name: query parameter.
            limit: query parameter.
            cursor: query parameter.
        """
        params: Dict[str, Any] = {}
        if status is not None:
            params["status"] = status
        if q is not None:
            params["q"] = q
        if tag is not None:
            params["tag"] = tag
        if channel is not None:
            params["channel"] = channel
        if source is not None:
            params["source"] = source
        if agent_name is not None:
            params["agent_name"] = agent_name
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor
        return self._client._request("GET", "/emails", params=params)

    def resend(self, id_: str, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a message again

        Creates a new message rather than re-running the old row, and sends under the
        key that sent the original — so the allowlist, that key’s rate limit and
        approval mode all apply as they did the first time.

        Args:
            id_: path segment.
        """
        return self._client._request("POST", f"/emails/{id_}/resend", idempotency_key=idempotency_key)

    def send(self, from_: str, to: Union[str, List[str]], subject: Optional[str] = None, cc: Optional[Union[str, List[str]]] = None, bcc: Optional[Union[str, List[str]]] = None, reply_to: Optional[Union[str, List[str]]] = None, tags: Optional[List[str]] = None, html: Optional[str] = None, text: Optional[str] = None, headers: Optional[Dict[str, Any]] = None, template: Optional[str] = None, variables: Optional[Dict[str, Any]] = None, attachments: Optional[List[Dict[str, Any]]] = None, scheduled_at: Optional[str] = None, dry_run: Optional[bool] = None, channel: Optional[str] = None, source: Optional[str] = None, agent_name: Optional[str] = None, utm: Optional[Dict[str, Any]] = None, verify_before_send: Optional[bool] = None, marketing: Optional[bool] = None, allow_duplicate: Optional[bool] = None, dlp: Optional[bool] = None, cross_agent_cooldown: Optional[str] = None, priority: Optional[str] = None, ticket_aware: Optional[bool] = None, idempotency_key: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
        """
        Send an email

        Key-only. A cookie rides along automatically, and a send endpoint reachable by
        cookie is reachable by CSRF. Answers 202: accepted, not delivered — the API
        never calls a provider synchronously. Sending from the shared onboarding domain
        is capped per account for the lifetime of the account; verify your own domain to
        lift it. `cc` and `bcc` are recipients: they count against quota and are checked
        against the key allowlist and your suppression list exactly as `to` is.
        `reply_to` is not, and is checked against neither. Also accepted as replyTo.

        Args:
            from_: Required.
            to: Required.
            subject: Optional.
            cc: Optional.
            bcc: Optional.
            reply_to: Optional.
            tags: Optional.
            html: Optional.
            text: Optional.
            headers: Optional.
            template: A stored template's name or id, rendered with `variables`. An explicit `subject` overrides the template's.
            variables: Optional.
            attachments: Optional.
            scheduled_at: Also accepted as scheduledAt.
            dry_run: Validate, render and check suppression without sending. Also accepted as dryRun.
            channel: Channel provenance. One of: api, sdk, mcp, smtp, console. Anything else is refused with 400 invalid_channel.
            source: Source provenance. One of: backend, agent, automation, system. Anything else is refused with 400 invalid_source.
            agent_name: Attributed agent name, up to 128 characters — longer is refused with 400 invalid_agent_name, not truncated. Also accepted as agentName.
            utm: Optional.
            verify_before_send: Real-time recipient deliverability verification before enqueue. Refuses undeliverable recipients with 422 undeliverable_recipient and debits zero quota. Also accepted as verifyBeforeSend.
            marketing: RFC 8058 One-Click List-Unsubscribe Header. When true, automatically injects List-Unsubscribe and List-Unsubscribe-Post headers and routes to bulk sender pools.
            allow_duplicate: When true, bypasses the 5-minute rolling loop circuit breaker deduplication. Also accepted as allowDuplicate or bypass_loop_breaker.
            dlp: Outbound DLP secret & PII scanner control. Defaults to true. Set false to explicitly bypass secret scanning.
            cross_agent_cooldown: Cross-agent sliding contact cooldown window (e.g. "24h", "12h", "1h", "30m", or seconds). Also accepted as crossAgentCooldown.
            priority: Message priority tier: "auth" | "security" (P0), "support" (P1), "billing" (P2), "follow_up" (P3), "marketing" (P4). Higher priority preempts lower priority cooldowns.
            ticket_aware: When true, pauses and holds low-priority agent emails if the recipient has an open support ticket. Defaults to true for agent sends. Also accepted as ticketAware.
        """
        body: Dict[str, Any] = dict(extra)
        if from_ is not None:
            body["from"] = from_
        if to is not None:
            body["to"] = to
        if subject is not None:
            body["subject"] = subject
        if cc is not None:
            body["cc"] = cc
        if bcc is not None:
            body["bcc"] = bcc
        if reply_to is not None:
            body["reply_to"] = reply_to
        if tags is not None:
            body["tags"] = tags
        if html is not None:
            body["html"] = html
        if text is not None:
            body["text"] = text
        if headers is not None:
            body["headers"] = headers
        if template is not None:
            body["template"] = template
        if variables is not None:
            body["variables"] = variables
        if attachments is not None:
            body["attachments"] = attachments
        if scheduled_at is not None:
            body["scheduled_at"] = scheduled_at
        if dry_run is not None:
            body["dry_run"] = dry_run
        if channel is not None:
            body["channel"] = channel
        if source is not None:
            body["source"] = source
        if agent_name is not None:
            body["agent_name"] = agent_name
        if utm is not None:
            body["utm"] = utm
        if verify_before_send is not None:
            body["verify_before_send"] = verify_before_send
        if marketing is not None:
            body["marketing"] = marketing
        if allow_duplicate is not None:
            body["allow_duplicate"] = allow_duplicate
        if dlp is not None:
            body["dlp"] = dlp
        if cross_agent_cooldown is not None:
            body["cross_agent_cooldown"] = cross_agent_cooldown
        if priority is not None:
            body["priority"] = priority
        if ticket_aware is not None:
            body["ticket_aware"] = ticket_aware
        return self._client._request("POST", "/emails", body=body, idempotency_key=idempotency_key)


class Inbound:
    """`client.inbound` — 2 operations."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def parse(self, raw_mime: Optional[str] = None, from_: Optional[str] = None, to: Optional[List[str]] = None, cc: Optional[List[str]] = None, subject: Optional[str] = None, text: Optional[str] = None, html: Optional[str] = None, message_id: Optional[str] = None, in_reply_to: Optional[str] = None, references: Optional[str] = None, headers: Optional[Dict[str, Any]] = None, idempotency_key: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
        """
        Context-safe inbound email parser, thread stitcher & prompt-injection classifier

        Parses inbound emails (JSON or raw RFC 822 MIME), stitches conversation threads
        (In-Reply-To/References), strips quoted reply chains and signatures (~85% token
        reduction), and tags prompt-injection risk score (0.0 to 1.0) with quarantine
        recommendations.

        Args:
            raw_mime: Raw RFC 822 MIME email payload string or buffer
            from_: Sender address
            to: Optional.
            cc: Optional.
            subject: Email subject line
            text: Plain text email content
            html: HTML email content
            message_id: RFC 5322 Message-ID header
            in_reply_to: RFC 5322 In-Reply-To header
            references: RFC 5322 References header
            headers: Optional.
        """
        body: Dict[str, Any] = dict(extra)
        if raw_mime is not None:
            body["rawMime"] = raw_mime
        if from_ is not None:
            body["from"] = from_
        if to is not None:
            body["to"] = to
        if cc is not None:
            body["cc"] = cc
        if subject is not None:
            body["subject"] = subject
        if text is not None:
            body["text"] = text
        if html is not None:
            body["html"] = html
        if message_id is not None:
            body["messageId"] = message_id
        if in_reply_to is not None:
            body["inReplyTo"] = in_reply_to
        if references is not None:
            body["references"] = references
        if headers is not None:
            body["headers"] = headers
        return self._client._request("POST", "/inbound/parse", body=body, idempotency_key=idempotency_key)

    def simulate(self, to: Optional[str] = None, recipient: Optional[str] = None, from_: Optional[str] = None, sender: Optional[str] = None, subject: Optional[str] = None, text: Optional[str] = None, html: Optional[str] = None, headers: Optional[Dict[str, Any]] = None, idempotency_key: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
        """
        Simulate receiving inbound email and test routing (Task 29)

        Simulates receiving an inbound email message, executes pattern matching against
        configured routes, stores message record, and optionally dispatches webhook
        payload. Requires Pro plan or above.

        Args:
            to: Recipient address to test route matching against
            recipient: Alternative field for recipient address
            from_: Sender email address
            sender: Alternative field for sender email address
            subject: Test email subject
            text: Plain text body
            html: HTML body
            headers: Optional.
        """
        body: Dict[str, Any] = dict(extra)
        if to is not None:
            body["to"] = to
        if recipient is not None:
            body["recipient"] = recipient
        if from_ is not None:
            body["from"] = from_
        if sender is not None:
            body["sender"] = sender
        if subject is not None:
            body["subject"] = subject
        if text is not None:
            body["text"] = text
        if html is not None:
            body["html"] = html
        if headers is not None:
            body["headers"] = headers
        return self._client._request("POST", "/inbound/simulate", body=body, idempotency_key=idempotency_key)


class InboundMessages:
    """`client.inbound_messages` — 2 operations."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def get(self, id_: str) -> Dict[str, Any]:
        """
        Get inbound email message details and parsed content (Task 29)

        Retrieves full details of a parsed inbound email message including clean
        markdown, stripped signatures, RFC 8601 authentication verdicts, and raw
        headers. Requires Pro plan or above.

        Args:
            id_: path segment.
        """
        return self._client._request("GET", f"/inbound/messages/{id_}")

    def list(self, limit: Optional[Any] = None, offset: Optional[Any] = None, recipient: Optional[Any] = None) -> Dict[str, Any]:
        """
        List received inbound email messages (Task 29)

        Lists parsed incoming email messages with pagination and optional recipient
        filtering. Requires Pro plan or above.

        Args:
            limit: query parameter.
            offset: query parameter.
            recipient: query parameter.
        """
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if recipient is not None:
            params["recipient"] = recipient
        return self._client._request("GET", "/inbound/messages", params=params)


class InboundRoutes:
    """`client.inbound_routes` — 5 operations."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def create(self, pattern: str, description: Optional[str] = None, target_type: Optional[str] = None, webhook_id: Optional[str] = None, webhook_url: Optional[str] = None, filter_spam: Optional[bool] = None, strip_signatures: Optional[bool] = None, priority: Optional[int] = None, active: Optional[bool] = None, idempotency_key: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
        """
        Create inbound MX routing rule (Task 29)

        Creates a custom inbound MX email routing rule with pattern matching (exact
        address, domain wildcard, prefix wildcard, or catch-all) and webhook forwarding.
        Requires Pro plan or above.

        Args:
            pattern: Address pattern to match (e.g. support@*, *@inbound.example.com, tickets+*@domain.com, *)
            description: Optional administrative description of this route
            target_type: Target handler type: webhook
            webhook_id: Optional existing webhook ID to dispatch received emails to
            webhook_url: Optional direct HTTP/HTTPS endpoint URL to receive signed payloads
            filter_spam: Whether to quarantine messages failing SPF, DKIM, or DMARC
            strip_signatures: Whether to strip email disclaimers and client signatures
            priority: Evaluation priority order (1-100, lower numbers evaluated first)
            active: Whether this route is currently active
        """
        body: Dict[str, Any] = dict(extra)
        if pattern is not None:
            body["pattern"] = pattern
        if description is not None:
            body["description"] = description
        if target_type is not None:
            body["targetType"] = target_type
        if webhook_id is not None:
            body["webhookId"] = webhook_id
        if webhook_url is not None:
            body["webhookUrl"] = webhook_url
        if filter_spam is not None:
            body["filterSpam"] = filter_spam
        if strip_signatures is not None:
            body["stripSignatures"] = strip_signatures
        if priority is not None:
            body["priority"] = priority
        if active is not None:
            body["active"] = active
        return self._client._request("POST", "/inbound/routes", body=body, idempotency_key=idempotency_key)

    def delete(self, id_: str) -> Dict[str, Any]:
        """
        Delete inbound MX routing rule (Task 29)

        Permanently removes an inbound MX routing rule. Requires Pro plan or above.

        Args:
            id_: path segment.
        """
        return self._client._request("DELETE", f"/inbound/routes/{id_}")

    def get(self, id_: str) -> Dict[str, Any]:
        """
        Get inbound MX routing rule details (Task 29)

        Retrieves details and configuration for a single inbound MX routing rule by ID.
        Requires Pro plan or above.

        Args:
            id_: path segment.
        """
        return self._client._request("GET", f"/inbound/routes/{id_}")

    def list(self) -> Dict[str, Any]:
        """
        List configured inbound MX routing rules (Task 29)

        Lists all active and configured inbound MX routing rules for the authenticated
        account, sorted by priority. Requires Pro plan or above.
        """
        return self._client._request("GET", "/inbound/routes")

    def update(self, id_: str, pattern: Optional[str] = None, description: Optional[str] = None, target_type: Optional[str] = None, webhook_id: Optional[str] = None, webhook_url: Optional[str] = None, filter_spam: Optional[bool] = None, strip_signatures: Optional[bool] = None, priority: Optional[int] = None, active: Optional[bool] = None, idempotency_key: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
        """
        Update inbound MX routing rule (Task 29)

        Updates attributes (pattern, webhookUrl, priority, active, spam filter) of an
        inbound MX route. Requires Pro plan or above.

        Args:
            id_: path segment.
            pattern: Updated address matching pattern
            description: Updated route description
            target_type: Updated target type
            webhook_id: Updated associated webhook UUID
            webhook_url: Updated target webhook URL
            filter_spam: Updated spam filter toggle
            strip_signatures: Updated signature stripping toggle
            priority: Updated execution priority (1-100)
            active: Updated active status
        """
        body: Dict[str, Any] = dict(extra)
        if pattern is not None:
            body["pattern"] = pattern
        if description is not None:
            body["description"] = description
        if target_type is not None:
            body["targetType"] = target_type
        if webhook_id is not None:
            body["webhookId"] = webhook_id
        if webhook_url is not None:
            body["webhookUrl"] = webhook_url
        if filter_spam is not None:
            body["filterSpam"] = filter_spam
        if strip_signatures is not None:
            body["stripSignatures"] = strip_signatures
        if priority is not None:
            body["priority"] = priority
        if active is not None:
            body["active"] = active
        return self._client._request("PATCH", f"/inbound/routes/{id_}", body=body, idempotency_key=idempotency_key)


class Inboxes:
    """`client.inboxes` — 8 operations."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def delete(self, id_: str) -> Dict[str, Any]:
        """
        Delete and expire an ephemeral inbox immediately

        Immediately removes an ephemeral agent inbox and flushes all associated messages
        from Redis and memory.

        Args:
            id_: path segment.
        """
        return self._client._request("DELETE", f"/inboxes/{id_}")

    def ephemeral(self, alias: Optional[str] = None, domain: Optional[str] = None, ttl_seconds: Optional[int] = None, description: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None, idempotency_key: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
        """
        Provision an ephemeral agent inbox (Task 7)

        Provisions a dynamic temporary inbox in under 10ms with automatic TTL expiration
        (default: 10 minutes / 600s). Designed for autonomous browser agents
        (Playwright, Cypress, Stagehand) to receive OTPs and solve 2FA challenges.
        Requires Pro plan ($19/mo) or above.

        Args:
            alias: Optional custom username prefix (e.g. agent-checkout-42)
            domain: Custom or system ephemeral domain (default auth.sadasend.com)
            ttl_seconds: Inbox lifetime in seconds (60 to 3600; default 600)
            description: Optional human-readable description of the agent task
            metadata: Optional.
        """
        body: Dict[str, Any] = dict(extra)
        if alias is not None:
            body["alias"] = alias
        if domain is not None:
            body["domain"] = domain
        if ttl_seconds is not None:
            body["ttlSeconds"] = ttl_seconds
        if description is not None:
            body["description"] = description
        if metadata is not None:
            body["metadata"] = metadata
        return self._client._request("POST", "/inboxes/ephemeral", body=body, idempotency_key=idempotency_key)

    def get(self, id_: str) -> Dict[str, Any]:
        """
        Get ephemeral inbox details

        Retrieves metadata, remaining lifetime, and latest OTP verification code for an
        ephemeral inbox.

        Args:
            id_: path segment.
        """
        return self._client._request("GET", f"/inboxes/{id_}")

    def inbound(self, to: str, from_: Optional[str] = None, subject: Optional[str] = None, text: Optional[str] = None, html: Optional[str] = None, idempotency_key: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
        """
        Ingest inbound email into an ephemeral inbox

        Ingests an inbound message targeting an ephemeral inbox, extracts 6-digit OTP
        codes and authentication magic links, and broadcasts to active SSE/WebSocket
        streams in under 150ms.

        Args:
            to: Recipient ephemeral inbox address
            from_: Sender email address
            subject: Email subject line
            text: Plain text message body
            html: HTML message body
        """
        body: Dict[str, Any] = dict(extra)
        if to is not None:
            body["to"] = to
        if from_ is not None:
            body["from"] = from_
        if subject is not None:
            body["subject"] = subject
        if text is not None:
            body["text"] = text
        if html is not None:
            body["html"] = html
        return self._client._request("POST", "/inboxes/inbound", body=body, idempotency_key=idempotency_key)

    def list(self) -> Dict[str, Any]:
        """
        List active ephemeral inboxes

        Lists all currently active ephemeral agent inboxes belonging to the
        authenticated account.
        """
        return self._client._request("GET", "/inboxes")

    def messages(self, id_: str) -> Dict[str, Any]:
        """
        List received messages for an ephemeral inbox

        Returns all inbound emails received by the specified ephemeral inbox during its
        active lifetime.

        Args:
            id_: path segment.
        """
        return self._client._request("GET", f"/inboxes/{id_}/messages")

    def otp(self, id_: str, wait_for: Optional[Any] = None, timeout_ms: Optional[Any] = None, since: Optional[Any] = None) -> Dict[str, Any]:
        """
        Get or wait for OTP verification code on ephemeral inbox

        Returns the latest extracted OTP, or long-polls reactive pub/sub up to timeoutMs
        (default: 15s) until an OTP arrives in under 150ms. Eliminates polling loops in
        test suites.

        Args:
            id_: path segment.
            wait_for: query parameter.
            timeout_ms: query parameter.
            since: query parameter.
        """
        params: Dict[str, Any] = {}
        if wait_for is not None:
            params["waitFor"] = wait_for
        if timeout_ms is not None:
            params["timeoutMs"] = timeout_ms
        if since is not None:
            params["since"] = since
        return self._client._request("GET", f"/inboxes/{id_}/otp", params=params)

    def stream(self, id_: str) -> Dict[str, Any]:
        """
        Real-time Server-Sent Events (SSE) push stream for ephemeral inbox

        Connects a persistent Server-Sent Events (SSE) push stream for browser agents.
        Emits real-time "connected", "otp", and "message" events with sub-150ms latency.

        Args:
            id_: path segment.
        """
        return self._client._request("GET", f"/inboxes/{id_}/stream")


class Integrations:
    """`client.integrations` — 1 operation."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def slack(self) -> Dict[str, Any]:
        """
        Get current Slack integration configuration status
        """
        return self._client._request("GET", "/integrations/slack")


class Keys:
    """`client.keys` — 1 operation."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def list(self) -> Dict[str, Any]:
        """
        API keys
        """
        return self._client._request("GET", "/keys")


class KeysApprovals:
    """`client.keys_approvals` — 1 operation."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def list(self) -> Dict[str, Any]:
        """
        Sends held by an approval-mode key
        """
        return self._client._request("GET", "/keys/approvals")


class SupportTickets:
    """`client.support_tickets` — 2 operations."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def get(self, id_: str) -> Dict[str, Any]:
        """
        One ticket and its thread

        Args:
            id_: path segment.
        """
        return self._client._request("GET", f"/support/tickets/{id_}")

    def list(self) -> Dict[str, Any]:
        """
        Your tickets
        """
        return self._client._request("GET", "/support/tickets")


class Suppressions:
    """`client.suppressions` — 2 operations."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def add(self, address: str, reason: Optional[str] = None, idempotency_key: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
        """
        Suppress an address

        A caller cannot claim `hard_bounce`; anything added here is recorded as
        `manual`.

        Args:
            address: Required.
            reason: Optional.
        """
        body: Dict[str, Any] = dict(extra)
        if address is not None:
            body["address"] = address
        if reason is not None:
            body["reason"] = reason
        return self._client._request("POST", "/suppressions", body=body, idempotency_key=idempotency_key)

    def list(self, reason: Optional[Any] = None, q: Optional[Any] = None, limit: Optional[Any] = None) -> Dict[str, Any]:
        """
        Suppressed addresses

        Args:
            reason: query parameter.
            q: query parameter.
            limit: query parameter.
        """
        params: Dict[str, Any] = {}
        if reason is not None:
            params["reason"] = reason
        if q is not None:
            params["q"] = q
        if limit is not None:
            params["limit"] = limit
        return self._client._request("GET", "/suppressions", params=params)


class Team:
    """`client.team` — 1 operation."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def get(self) -> Dict[str, Any]:
        """
        Members, and invitations nobody has accepted yet
        """
        return self._client._request("GET", "/team")


class Templates:
    """`client.templates` — 4 operations."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def get(self, id_: str) -> Dict[str, Any]:
        """
        One template

        Args:
            id_: path segment.
        """
        return self._client._request("GET", f"/templates/{id_}")

    def list(self) -> Dict[str, Any]:
        """
        Templates, latest version of each

        A summary per template — not the full record. The bodies are deliberately
        absent: a list of twenty templates would otherwise carry twenty HTML documents
        to render a table of names. `GET /templates/:id` has `html`, `text` and
        `engine`.
        """
        return self._client._request("GET", "/templates")

    def render(self, id_: str, variables: Optional[Dict[str, Any]] = None, idempotency_key: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
        """
        Render without sending

        Args:
            id_: path segment.
            variables: Optional.
        """
        body: Dict[str, Any] = dict(extra)
        if variables is not None:
            body["variables"] = variables
        return self._client._request("POST", f"/templates/{id_}/render", body=body, idempotency_key=idempotency_key)

    def test(self, id_: str, to: str, variables: Optional[Dict[str, Any]] = None, idempotency_key: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
        """
        Send a test email for a template

        Renders the template with test variables and dispatches a preview email with
        [Test] subject prefix.

        Args:
            id_: path segment.
            to: Required.
            variables: Optional.
        """
        body: Dict[str, Any] = dict(extra)
        if to is not None:
            body["to"] = to
        if variables is not None:
            body["variables"] = variables
        return self._client._request("POST", f"/templates/{id_}/test", body=body, idempotency_key=idempotency_key)


class Testing:
    """`client.testing` — 2 operations."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def inbound(self, to: Optional[str] = None, from_: Optional[str] = None, subject: Optional[str] = None, text: Optional[str] = None, html: Optional[str] = None, idempotency_key: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
        """
        Ingest inbound test email and extract OTP/magic-link (Task 27)

        Ingests an inbound test email into a wildcard test inbox (*@test.sadasend.com),
        extracts 6-digit OTP verification codes and magic links, and broadcasts to
        active test runners via Redis pub/sub. Requires Pro plan ($19/mo) or above.

        Args:
            to: Recipient test inbox address (e.g. signup-test@test.sadasend.com)
            from_: Sender email address
            subject: Email subject line
            text: Plain text email content
            html: HTML email content
        """
        body: Dict[str, Any] = dict(extra)
        if to is not None:
            body["to"] = to
        if from_ is not None:
            body["from"] = from_
        if subject is not None:
            body["subject"] = subject
        if text is not None:
            body["text"] = text
        if html is not None:
            body["html"] = html
        return self._client._request("POST", "/testing/inbound", body=body, idempotency_key=idempotency_key)

    def wait_for_code(self, to: Optional[str] = None, timeout_ms: Optional[int] = None, since: Optional[str] = None, idempotency_key: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
        """
        Wait for OTP or magic link code with JSON payload (waitForCode)

        Wait for an OTP or magic link sent to a test inbox with JSON request body
        options (to, timeoutMs, since). Requires Pro plan ($19/mo) or above.

        Args:
            to: Recipient test inbox address (e.g. agent-99@test.sadasend.com)
            timeout_ms: Maximum wait duration in milliseconds (100 to 60000; default 15000)
            since: Optional ISO timestamp or epoch milliseconds filter
        """
        body: Dict[str, Any] = dict(extra)
        if to is not None:
            body["to"] = to
        if timeout_ms is not None:
            body["timeoutMs"] = timeout_ms
        if since is not None:
            body["since"] = since
        return self._client._request("POST", "/testing/wait-for-code", body=body, idempotency_key=idempotency_key)


class TestingInboxes:
    """`client.testing_inboxes` — 2 operations."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def code(self, email: str, timeout_ms: Optional[Any] = None, since: Optional[Any] = None) -> Dict[str, Any]:
        """
        Wait for OTP or magic link code on a test inbox (waitForCode)

        Long-polls a wildcard test inbox up to timeoutMs (default 15s) using sub-100ms
        Redis pub/sub. Resolves immediately when a matching verification code or auth
        link lands. Requires Pro plan ($19/mo) or above.

        Args:
            email: path segment.
            timeout_ms: query parameter.
            since: query parameter.
        """
        params: Dict[str, Any] = {}
        if timeout_ms is not None:
            params["timeoutMs"] = timeout_ms
        if since is not None:
            params["since"] = since
        return self._client._request("GET", f"/testing/inboxes/{email}/code", params=params)

    def latest(self, email: str) -> Dict[str, Any]:
        """
        Get latest test message received by test inbox

        Returns the most recent test message received by the specified test inbox within
        the 5-minute retention window without waiting.

        Args:
            email: path segment.
        """
        return self._client._request("GET", f"/testing/inboxes/{email}/latest")


class Tools:
    """`client.tools` — 5 operations."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def check(self, check: str, subject: str, selector: Optional[str] = None, idempotency_key: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
        """
        Run a free deliverability check

        No authentication, and we do not record what people check.

        Args:
            check: path segment.
            subject: Required.
            selector: DKIM only, and optional — common selectors are probed.
        """
        body: Dict[str, Any] = dict(extra)
        if subject is not None:
            body["subject"] = subject
        if selector is not None:
            body["selector"] = selector
        return self._client._request("POST", f"/tools/{check}", body=body, idempotency_key=idempotency_key)

    def list(self) -> Dict[str, Any]:
        """
        Which free checks this deployment knows about
        """
        return self._client._request("GET", "/tools")

    def utm(self, url: str, source: Optional[str] = None, medium: Optional[str] = None, campaign: Optional[str] = None, term: Optional[str] = None, content: Optional[str] = None, override_existing: Optional[bool] = None, idempotency_key: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
        """
        Build and normalize standardized UTM campaign URLs

        Injects or merges UTM tracking parameters into target URLs while preserving
        existing parameters, ports, paths, and anchors. No authentication required.

        Args:
            url: The destination web URL to tag.
            source: The campaign source (e.g. newsletter, agent_claude).
            medium: The marketing medium (e.g. email, cpc).
            campaign: The specific campaign name.
            term: The search term or trigger keyword.
            content: The specific link or CTA identifier.
            override_existing: Whether to override existing UTM parameters if already present.
        """
        body: Dict[str, Any] = dict(extra)
        if url is not None:
            body["url"] = url
        if source is not None:
            body["source"] = source
        if medium is not None:
            body["medium"] = medium
        if campaign is not None:
            body["campaign"] = campaign
        if term is not None:
            body["term"] = term
        if content is not None:
            body["content"] = content
        if override_existing is not None:
            body["override_existing"] = override_existing
        return self._client._request("POST", "/tools/utm", body=body, idempotency_key=idempotency_key)

    def verify(self, email: Optional[str] = None, subject: Optional[str] = None, idempotency_key: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
        """
        Verify recipient email deliverability in real-time

        Sub-50ms recipient verification engine. Validates RFC 5322 syntax, queries live
        DNS MX servers, identifies disposable burner mailboxes, detects role
        distribution addresses, and suggests typo corrections (e.g. gmaill.com ->
        gmail.com). Unauthenticated guest requests are limited to 5 checks/day;
        authenticated requests consume verification credits.

        Args:
            email: The recipient email address to verify (e.g. "alex@example.com"). Also accepted as `subject`.
            subject: Alternative alias for `email`.
        """
        body: Dict[str, Any] = dict(extra)
        if email is not None:
            body["email"] = email
        if subject is not None:
            body["subject"] = subject
        return self._client._request("POST", "/tools/verify", body=body, idempotency_key=idempotency_key)

    def verify_batch(self, emails: List[str], idempotency_key: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
        """
        Batch verify recipient email deliverability

        High-throughput bulk email verification engine. Gated by plan tier: Starter (up
        to 100/batch), Pro (up to 1,000/batch), Scale (up to 10,000/batch). Consumes
        verification quota/credits per email.

        Args:
            emails: Required.
        """
        body: Dict[str, Any] = dict(extra)
        if emails is not None:
            body["emails"] = emails
        return self._client._request("POST", "/tools/verify/batch", body=body, idempotency_key=idempotency_key)


class Webhooks:
    """`client.webhooks` — 2 operations."""

    def __init__(self, client: "SadaSend") -> None:
        self._client = client

    def deliveries(self, id_: str, limit: Optional[Any] = None, event: Optional[Any] = None) -> Dict[str, Any]:
        """
        Every delivery attempt for one endpoint

        Successes included. "You never sent it" is answered by a success row with a
        status the endpoint returned, and that is the row the question usually needs.

        Args:
            id_: path segment.
            limit: query parameter.
            event: query parameter.
        """
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if event is not None:
            params["event"] = event
        return self._client._request("GET", f"/webhooks/{id_}/deliveries", params=params)

    def list(self) -> Dict[str, Any]:
        """
        Webhook endpoints
        """
        return self._client._request("GET", "/webhooks")


#: Attribute name to resource class, wired up by SadaSend.__init__.
RESOURCES = {
    "account": Account,
    "arbiter": Arbiter,
    "arbiter_recipients": ArbiterRecipients,
    "arbiter_tickets": ArbiterTickets,
    "dmarc": Dmarc,
    "dmarc_domains": DmarcDomains,
    "dmarc_reports": DmarcReports,
    "domains": Domains,
    "emails": Emails,
    "inbound": Inbound,
    "inbound_messages": InboundMessages,
    "inbound_routes": InboundRoutes,
    "inboxes": Inboxes,
    "integrations": Integrations,
    "keys": Keys,
    "keys_approvals": KeysApprovals,
    "support_tickets": SupportTickets,
    "suppressions": Suppressions,
    "team": Team,
    "templates": Templates,
    "testing": Testing,
    "testing_inboxes": TestingInboxes,
    "tools": Tools,
    "webhooks": Webhooks,
}
