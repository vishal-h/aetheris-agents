#!/usr/bin/env python3
"""Re-record the GitHub fixtures from a live organisation. Operator-run, not collected by pytest.

The committed `github_*.json` fixtures are raw REST response bodies — what the adapter's client
receives — pseudonymised of everything identifying the account, its people, or its internal
structure. This script is how they are refreshed: it reuses the adapter's own client and token
loader (so it authenticates exactly the way the adapter does), calls each endpoint the sweep
makes, scrubs, and writes the files.

Run it under the D2 hermetic prefix, from the repo root:

    set -a; . ~/.secrets/github-cloudcost.env; set +a
    env -u GH_TOKEN -u GITHUB_TOKEN -u GH_ENTERPRISE_TOKEN \\
        -u GITHUB_ENTERPRISE_TOKEN -u GITHUB_PERSONAL_ACCESS_TOKEN \\
        python3 cloudcost/tests/record_github_fixtures.py --out /tmp/recorded-github

It writes to `--out` (default: a scratch dir), never over `tests/fixtures/` directly — a
recording is reviewed before it replaces a committed fixture.

**Scrubbing is code, not a manual pass.** A recording that still carries a real identifier is a
defect this script must catch, not the reviewer. The placeholder mapping is first-seen-order and
deterministic, so re-recording the same organisation produces byte-identical fixtures except
where the organisation itself changed. What is *not* stable across runs, by construction: seat
`last_activity_at` / `last_authenticated_at` / `updated_at`, and every figure for an in-flight
month. The committed fixtures therefore pin a **settled** period, not the current one.

**The class that is scrubbed, defined rather than enumerated** (m6 t2 §U2). Anything identifying
the account, the people in it, or its internal structure: organisation, repositories, logins,
display names, numeric user ids, node ids, profile and avatar URLs, email addresses. Explicitly
NOT scrubbed, because these carry the tests' meaning: monetary figures, product/SKU/unitType
strings, quantities, timestamps, and the period fields. `last_activity_editor` is a tool version
string (`vscode/1.132.1/copilot-chat/0.60.0`) and is neither an identity nor load-bearing — kept,
and named here as an examined member of neither class rather than left unmentioned.

**Why the identity map is ordinal rather than a fixed constant.** `record_aws_fixtures.py` scrubs
by substituting a single literal (`\\b\\d{12}\\b` -> `111122223333`), which is stable but collapses
distinct values onto one. That is right for an account id, of which there is one, and wrong here:
six seats belonging to six people must stay six distinguishable people or every relational
assertion in `test_fetch_github.py` becomes vacuous. So this follows
`record_linode_fixtures.py`'s `Scrubber` instead — stable, first-seen-order, deterministic — and
the two recorders differ on exactly this point, deliberately.

This file deliberately does **not** import from either sibling recorder — a CLI-to-CLI import is
the anti-pattern named at `_normalized.py:35-37`. The shape and posture are copied; the identity
map, the endpoint list and the findings report are GitHub's own.

It also prints a **findings report** to stdout: the evidence for the questions t2 and t3 settle
from live reads rather than from documentation — the D7 reconcile margin, whether any seat
carries a lifecycle signal, and whether either billing endpoint has grown a currency field.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import fetch_github  # noqa: E402

#: A GitHub credential is `ghp_`/`gho_`/`ghu_`/`ghs_`/`ghr_` + 36, or `github_pat_` + more.
#: Any string of that shape is replaced wherever it appears, whatever key carries it — a
#: credential must never survive into a fixture even if the API starts returning one under a
#: name this script does not know.
TOKEN_SHAPED = re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{20,})\b")

#: Keys whose entire value is an identity and is replaced wholesale rather than by mapping.
SCRUB_KEYS = {
    "email": "cloudcost@example.invalid",
    "gravatar_id": "",
    "name": "Cloudcost Placeholder",
    "company": "Example Org",
}

#: Keys carrying a login-shaped identity, wherever they appear.
LOGIN_KEYS = ("login", "organization", "organizationName", "repositoryName")


class Scrubber:
    """Stable, first-seen-order pseudonym assignment across every recorded body.

    One instance is shared by the whole recording run, so a login seen in the seats response
    and the same login seen inside an avatar URL resolve to the same placeholder — which is
    what keeps a relational assertion meaningful after the scrub.

    Substitution is two-phase on purpose. Phase one walks the structure and *learns* every
    identity from the keys that carry one; phase two rewrites, and because the rewrite is a
    text substitution over every string it also catches the fifteen `*_url` fields, which
    embed the login and the numeric id and which no key-based table would reach.
    """

    def __init__(self, org_placeholder: str = "example-org") -> None:
        self.org_placeholder = org_placeholder
        #: real login -> placeholder, in first-seen order.
        self.logins: dict = {}
        #: real numeric user id -> placeholder id, in first-seen order.
        self.ids: dict = {}
        #: real repository name -> placeholder, in first-seen order.
        self.repos: dict = {}
        self.orgs: set = set()

    # ------------------------------------------------------------------ phase one: learn
    def learn(self, node, org: str | None = None) -> None:
        if org:
            self.orgs.add(org)
        if isinstance(node, dict):
            login = node.get("login")
            # `/user/orgs` rows carry `login` too, and it is the ORGANISATION's. Mapping it as
            # a person would give the org two different placeholders — `user-N` here and
            # `example-org` in the billing bodies — for one real name, which is precisely the
            # consistency the ordinal map exists to provide.
            is_org = isinstance(login, str) and login in self.orgs
            for key, value in node.items():
                if key in ("organization", "organizationName") and isinstance(value, str) and value:
                    self.orgs.add(value)
                elif key == "repositoryName" and isinstance(value, str) and value:
                    self.repos.setdefault(value, f"repo-{len(self.repos) + 1}")
                elif key == "login" and isinstance(value, str) and value and not is_org:
                    self.logins.setdefault(value, f"user-{len(self.logins) + 1}")
                elif key == "id" and isinstance(value, int) and value > 0:
                    # Only an id sitting beside a login is an account identifier — a user's or
                    # an organisation's, both of which are scrubbed. A billing row carries no
                    # `id` at all, so this cannot mis-fire on a monetary figure or a quantity.
                    if isinstance(login, str):
                        self.ids.setdefault(value, 10_000_000 + len(self.ids) + 1)
                self.learn(value)
        elif isinstance(node, list):
            for value in node:
                self.learn(value)

    # ----------------------------------------------------------------- phase two: rewrite
    def text(self, value: str) -> str:
        value = TOKEN_SHAPED.sub("TOKEN-SHAPED-VALUE-REDACTED", value)
        # Longest first, so a login that is a prefix of another is not half-replaced.
        for real, placeholder in sorted(self.logins.items(), key=lambda kv: -len(kv[0])):
            value = re.sub(rf"(?<![A-Za-z0-9-]){re.escape(real)}(?![A-Za-z0-9-])",
                           placeholder, value)
        for real, placeholder in sorted(self.repos.items(), key=lambda kv: -len(kv[0])):
            value = re.sub(rf"(?<![A-Za-z0-9-]){re.escape(real)}(?![A-Za-z0-9-])",
                           placeholder, value)
        for real in sorted(self.orgs, key=len, reverse=True):
            value = re.sub(rf"(?<![A-Za-z0-9-]){re.escape(real)}(?![A-Za-z0-9-])",
                           self.org_placeholder, value)
        for real, placeholder in sorted(self.ids.items(), key=lambda kv: -len(str(kv[0]))):
            value = re.sub(rf"(?<!\d){real}(?!\d)", str(placeholder), value)
        return value

    def walk(self, node):
        if isinstance(node, dict):
            out = {}
            for key, value in node.items():
                if key == "node_id" and isinstance(value, str):
                    # Regenerated rather than replaced: a GitHub node id is base64 of
                    # `04:User<id>`, so a fixture whose node id decoded to a different number
                    # than its own `id` field would be internally inconsistent in a way that is
                    # invisible until someone decodes it.
                    out[key] = self._node_id(value, node.get("id"))
                elif key in SCRUB_KEYS and not isinstance(value, (dict, list)):
                    out[key] = SCRUB_KEYS[key]
                elif key == "id" and isinstance(value, int) and value in self.ids:
                    out[key] = self.ids[value]
                else:
                    out[key] = self.walk(value)
            return out
        if isinstance(node, list):
            return [self.walk(item) for item in node]
        if isinstance(node, str):
            return self.text(node)
        return node

    def _node_id(self, original: str, real_id) -> str:
        """Rebuild a node id around the placeholder, or drop it.

        A node id is base64 of `04:User<id>`, so the real id hides inside it where no text
        substitution over the encoded string can reach — and where the scrub-verification test
        must decode to see it. The replacement targets the id itself: an earlier version
        rewrote the *first* run of digits, which is the `04` type prefix, and left the real id
        standing inside a value that looked scrubbed.
        """
        placeholder = self.ids.get(real_id)
        if placeholder is None:
            return "NODE-ID-REDACTED"
        try:
            decoded = base64.b64decode(original).decode()
        except Exception:  # noqa: BLE001 - an opaque node id is replaced, not parsed
            return "NODE-ID-REDACTED"
        rebuilt = re.sub(rf"(?<!\d){real_id}(?!\d)", str(placeholder), decoded)
        if str(real_id) in rebuilt:
            return "NODE-ID-REDACTED"
        return base64.b64encode(rebuilt.encode()).decode()


def record(client, stem: str, path: str, params: dict, recorded: dict, errors: list) -> None:
    """Capture one endpoint body whole, unscrubbed for now — the scrub runs once, at the end.

    Bodies are kept as the client receives them so the offline stub replays exactly the shape
    the provider returns, and so `usageItems` stays complete: the reconcile test sums every row
    against the summary's own total, and a trimmed capture would not reconcile.
    """
    try:
        recorded[stem] = client.get(path, params=params)
    except (fetch_github.GitHubAuthError, fetch_github.GitHubAPIError) as exc:
        errors.append({"source": stem, "error": str(exc)})


def findings(recorded: dict) -> dict:
    """The evidence for the questions t2 and t3 settle from live reads.

    Reported as data, not as a conclusion: this function states what was observed and never
    picks the mapping. `state` in particular is the adapter's decision, made by a human reading
    `seat_fields_present` below — the whole point is that a seat's lifecycle position is not
    inspectable from a field, because there is no field.
    """
    summary = recorded.get("github_billing_usage_summary") or {}
    detail = recorded.get("github_billing_usage_detail") or {}
    seats = (recorded.get("github_copilot_seats") or {}).get("seats") or []

    summary_items = summary.get("usageItems") or []
    detail_items = detail.get("usageItems") or []
    summary_total = sum(float(row.get("netAmount") or 0.0) for row in summary_items)
    detail_total = sum(float(row.get("netAmount") or 0.0) for row in detail_items)

    return {
        "D7 — summary vs detail reconcile": {
            "summary_items": len(summary_items),
            "detail_items": len(detail_items),
            "summary_total": summary_total,
            "detail_total": detail_total,
            "difference": detail_total - summary_total,
            "tolerance": fetch_github.RECONCILE_TOLERANCE,
            "note": (
                "D7 builds the cost snapshot from the summary endpoint ON THE GROUND that the "
                "two agree. If the difference here is not float-summation noise, the recording "
                "is evidence against D7 and must not be promoted to a fixture as though it "
                "confirmed it."
            ),
        },
        "seat lifecycle — is there a state field at all": {
            "seat_count": len(seats),
            "seat_fields_present": sorted({key for row in seats for key in row}),
            "pending_cancellation_values": sorted(
                {repr(row.get("pending_cancellation_date")) for row in seats}
            ),
            "last_activity_at_populated": sum(1 for row in seats if row.get("last_activity_at")),
            "note": (
                "A seat carries no status/state field. `state` is therefore null and "
                "`pending_cancellation_date` is carried nowhere — §Normalized admits no "
                "provider_extra on the inventory shape at either level. If a state field "
                "appears here in a later recording, that is a schema question for its own "
                "ticket, not something an adapter absorbs."
            ),
        },
        "D1 — currency field, structural sweep": {
            "summary": fetch_github.currency_field_names(summary),
            "detail": fetch_github.currency_field_names(detail),
            "note": (
                "Both must be empty. A non-empty list does not change the emitted currency "
                "(D1: adapter-declared, never captured) — it means `currency_basis` in "
                "fetch_github.py states something that is no longer true and must be rewritten."
            ),
        },
        "SKU spellings — the two endpoints do not agree, and it is not a case transform": {
            "summary": sorted(
                {f"{r.get('product')}/{r.get('sku')}/{r.get('unitType')}" for r in summary_items}
            ),
            "detail": sorted(
                {f"{r.get('product')}/{r.get('sku')}/{r.get('unitType')}" for r in detail_items}
            ),
        },
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Record GitHub fixtures from a live org")
    parser.add_argument("--out", default="/tmp/recorded-github")
    parser.add_argument("--org", default=None, help="default: the token's sole membership")
    parser.add_argument(
        "--period",
        default="2026-07",
        help="YYYY-MM to record; must be a SETTLED month, never the in-flight one",
    )
    parser.add_argument(
        "--empty-period",
        default="2025-01",
        help="a real YYYY-MM the org has no usage in, for the empty-month fixtures",
    )
    parser.add_argument("--api-base", default=fetch_github.DEFAULT_API_BASE)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    fetch_github.warn_shadowing_env()
    client = fetch_github.GitHubClient(
        token=fetch_github.load_token(), api_base=args.api_base
    )
    org = fetch_github.resolve_org(client, args.org)

    period = fetch_github.validate_period(args.period)
    empty = fetch_github.validate_period(args.empty_period)
    if period == fetch_github.current_period():
        print(
            f"refusing to record {period}: it is the in-flight month, and its figures change "
            f"between runs — pass --period with a settled month.",
            file=sys.stderr,
        )
        return 1

    year, month = fetch_github.period_parts(period)
    empty_year, empty_month = fetch_github.period_parts(empty)
    billing = f"/organizations/{org}/settings/billing/usage"

    recorded: dict = {}
    errors: list = []
    record(client, "github_billing_usage_summary", f"{billing}/summary",
           {"year": year, "month": month}, recorded, errors)
    record(client, "github_billing_usage_detail", billing,
           {"year": year, "month": month}, recorded, errors)
    record(client, "github_billing_usage_summary_empty", f"{billing}/summary",
           {"year": empty_year, "month": empty_month}, recorded, errors)
    record(client, "github_billing_usage_detail_empty", billing,
           {"year": empty_year, "month": empty_month}, recorded, errors)
    record(client, "github_copilot_seats", f"/orgs/{org}/copilot/billing/seats",
           {"per_page": fetch_github.PAGE_SIZE}, recorded, errors)
    record(client, "github_user_orgs", "/user/orgs", {"per_page": fetch_github.PAGE_SIZE},
           recorded, errors)

    # The findings report reads the LIVE bodies: it is evidence about the account, and a
    # pseudonymised body would tell the reader about the scrub instead.
    report_findings = findings(recorded)

    scrubber = Scrubber()
    for body in recorded.values():
        scrubber.learn(body, org=org)

    comment = (
        f"RECORDED from GitHub for {period} and pseudonymised by "
        f"tests/record_github_fixtures.py (organisation, repositories, logins, user ids, node "
        f"ids, profile and avatar URLs, emails). Monetary figures, SKU names, quantities and "
        f"timestamps are REAL and load-bearing. "
        f"Replace this line with what the fixture proves before committing."
    )

    written = []
    list_bodied = []
    for stem, body in recorded.items():
        scrubbed = scrubber.walk(body)
        if isinstance(scrubbed, list):
            # `/user/orgs` answers with a bare JSON array. The stub replays a fixture verbatim
            # as the response body, so this one cannot carry the `_comment` first key the rest
            # do — a wrapper object would change the shape the adapter parses, which is the one
            # thing a recording must not do. Named in the report and exempted by name in
            # `test_every_github_fixture_documents_what_it_proves`, rather than silently
            # weakening that test to containment.
            payload = scrubbed
            list_bodied.append(f"{stem}.json")
        else:
            payload = {"_comment": comment, **scrubbed}
        (out / f"{stem}.json").write_text(json.dumps(payload, indent=2) + "\n")
        written.append(f"{stem}.json")

    report = {
        "out": str(out),
        "period": period,
        "empty_period": empty,
        "written": sorted(written),
        "list_bodied_no_comment": sorted(list_bodied),
        "identities_mapped": {
            "logins": len(scrubber.logins),
            "numeric_ids": len(scrubber.ids),
            "repositories": len(scrubber.repos),
            "organisations": len(scrubber.orgs),
        },
        "findings": report_findings,
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
