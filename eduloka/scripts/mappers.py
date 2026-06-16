"""Stage-2 (map): pure transforms from a raw fetch envelope to an EduxRecord.

No I/O — testable with plain data, re-runnable over captured raw JSONL.
Sets full `text` where the provider gives it (Exa) and derives a lean display
`snippet`; enrichment starts empty and is filled later by workers.
"""

from __future__ import annotations

from edux_record import EduxRecord

SNIPPET_LEN = 300


def display_snippet(text: str | None, limit: int = SNIPPET_LEN) -> str | None:
    if not isinstance(text, str):
        return None
    text = text.strip()
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


def map_cse(raw: dict, *, term=None, fetched_at=None) -> EduxRecord:
    # CSE is the one provider with real pagemap: populate image + metatags for real.
    pagemap = raw.get("pagemap") or {}
    cse_image = pagemap.get("cse_image") or []
    image = cse_image[0].get("src") if cse_image and isinstance(cse_image[0], dict) else None
    return EduxRecord(
        link=raw.get("link"),
        title=raw.get("title"),
        snippet=raw.get("snippet"),
        image=image,
        text=None,  # CSE returns no full page text; needs a fetch-text worker
        search_term=term,
        source_provider="cse",
        fetched_at=fetched_at,
        metatags=pagemap.get("metatags") or [],
    )


def map_serper(raw: dict, *, term=None, fetched_at=None) -> EduxRecord:
    return EduxRecord(
        link=raw.get("link"),
        title=raw.get("title"),
        snippet=raw.get("snippet"),
        image=raw.get("imageUrl") or raw.get("thumbnailUrl"),
        text=None,  # SERP snippet only; full text needs a fetch-text worker
        search_term=term,
        source_provider="serper",
        fetched_at=fetched_at,
        metatags=[{k: raw[k] for k in ("position", "date", "sitelinks") if k in raw}],
    )


def map_dataforseo(raw: dict, *, term=None, fetched_at=None) -> EduxRecord:
    return EduxRecord(
        link=raw.get("url"),
        title=raw.get("title"),
        snippet=raw.get("description"),
        image=raw.get("image_url"),
        text=None,  # SERP only; full text needs a fetch-text worker
        search_term=term,
        source_provider="dataforseo",
        fetched_at=fetched_at,
        metatags=[{k: raw[k] for k in ("rank_absolute", "domain") if k in raw}],
    )


def map_exa(raw: dict, *, term=None, fetched_at=None) -> EduxRecord:
    text = raw.get("text") if isinstance(raw.get("text"), str) else None
    return EduxRecord(
        link=raw.get("url"),
        title=raw.get("title"),
        snippet=display_snippet(text),
        image=raw.get("image"),
        text=text,
        search_term=term,
        source_provider="exa",
        fetched_at=fetched_at,
        metatags=[{k: raw[k] for k in ("score", "publishedDate", "author") if k in raw}],
    )


MAPPERS = {
    "cse": map_cse,
    "serper": map_serper,
    "dataforseo": map_dataforseo,
    "exa": map_exa,
}


def map_envelope(env: dict) -> EduxRecord:
    provider = env.get("provider")
    fn = MAPPERS.get(provider)
    if fn is None:
        raise ValueError(f"no mapper for provider {provider!r}")
    return fn(env.get("raw", {}), term=env.get("term"), fetched_at=env.get("fetched_at"))
