"""
Generated from openapi.json. DO NOT EDIT.

Run `bun run sdk:python` to regenerate. CI runs `bun run sdk:python:check`, which
regenerates and fails on any difference — so a route added in the morning is in this
file before that morning's pull request can land.

Only the operations live here. The transport, retries, error classes and webhook
verifier are hand-written in _client.py, errors.py and webhooks.py — a generator cannot
write "obey Retry-After" or "never retry a guardrail refusal", and those are the whole
point of the client.

Operations reachable with an API key: 33. Cookie-session-only operations excluded: 46 —
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

    def send(self, from_: str, to: Union[str, List[str]], subject: Optional[str] = None, cc: Optional[Union[str, List[str]]] = None, bcc: Optional[Union[str, List[str]]] = None, reply_to: Optional[Union[str, List[str]]] = None, tags: Optional[List[str]] = None, html: Optional[str] = None, text: Optional[str] = None, headers: Optional[Dict[str, Any]] = None, template: Optional[str] = None, variables: Optional[Dict[str, Any]] = None, attachments: Optional[List[Dict[str, Any]]] = None, scheduled_at: Optional[str] = None, dry_run: Optional[bool] = None, channel: Optional[str] = None, source: Optional[str] = None, agent_name: Optional[str] = None, utm: Optional[Dict[str, Any]] = None, verify_before_send: Optional[bool] = None, marketing: Optional[bool] = None, idempotency_key: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
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
        return self._client._request("POST", "/emails", body=body, idempotency_key=idempotency_key)


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
    "domains": Domains,
    "emails": Emails,
    "keys": Keys,
    "keys_approvals": KeysApprovals,
    "support_tickets": SupportTickets,
    "suppressions": Suppressions,
    "team": Team,
    "templates": Templates,
    "tools": Tools,
    "webhooks": Webhooks,
}
