"""EduxRecord — the eduloka silver/edux schema.

Fields
------
Core (1:1 with gws_cse):
  link, title, snippet, image, search_term, metatags

Lake / enrichment fuel (not written to gws_cse):
  text (full page text — only Exa provides inline; SERP providers need a worker)

Provenance:
  source_provider, fetched_at

Enrichment bag:
  enrichment (jsonb; namespaced per enricher, e.g. {"keywords": {"_by": ..., "_at": ...}})

to_gws_cse() produces the operational row: core + enrichment. text is excluded.
Provenance is folded into a trailing _edux entry appended to metatags.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EduxRecord:
    link: str | None = None
    title: str | None = None
    snippet: str | None = None
    image: str | None = None
    text: str | None = None
    search_term: str | None = None
    source_provider: str | None = None
    fetched_at: str | None = None
    metatags: list = field(default_factory=list)
    enrichment: dict = field(default_factory=dict)
    status: int = 1

    def to_dict(self) -> dict:
        return {
            "link": self.link,
            "title": self.title,
            "snippet": self.snippet,
            "image": self.image,
            "text": self.text,
            "search_term": self.search_term,
            "source_provider": self.source_provider,
            "fetched_at": self.fetched_at,
            "metatags": list(self.metatags),
            "enrichment": dict(self.enrichment),
            "status": self.status,
        }

    def to_gws_cse(self) -> dict:
        # Append provenance as a trailing _edux entry; existing metatag entries untouched.
        provenance = {"_edux": {"source_provider": self.source_provider, "fetched_at": self.fetched_at}}
        return {
            "link": self.link,
            "title": self.title,
            "snippet": self.snippet,
            "image": self.image,
            "search_term": self.search_term,
            "status": self.status,
            "metatags": list(self.metatags) + [provenance],
            "enrichment": dict(self.enrichment),
        }
