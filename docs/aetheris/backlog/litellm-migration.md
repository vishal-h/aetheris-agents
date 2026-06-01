# Backlog: LiteLLM Proxy Migration

**Status:** Backlog — implement after P6 (token/cost surface in Rig) is stable
**Depends on:** pricing.ex + cost_usd landed (harness vNext #34)

---

## Why

The current harness has three separate LLM adapters (Anthropic, Ollama, Gemini),
a manually maintained pricing table (`pricing.ex`), and no support for prompt
cache token pricing. LiteLLM proxy addresses all of these:

| Problem now | LiteLLM solution |
|-------------|-----------------|
| Pricing table drifts — manual updates needed per model/price change | Pricing maintained externally by LiteLLM, updated automatically |
| Three separate Elixir adapters to maintain | One OpenAI-compatible adapter hits `localhost:4000` |
| Cache tokens (`cache_read_input_tokens`, `cache_creation_input_tokens`) not captured or priced | LiteLLM handles Anthropic cache pricing automatically |
| No cross-provider spend tracking | Built-in `/spend` endpoint, per-model/per-tag cost tracking |
| Adding a new provider = new Elixir adapter | Adding a new provider = LiteLLM config change |

---

## What LiteLLM is

LiteLLM proxy is a Python service that sits between the harness and all LLM
providers. It presents a single OpenAI-compatible API (`/v1/messages` or
`/v1/chat/completions`) regardless of the underlying provider. The harness
sends all LLM calls to `http://localhost:4000` and LiteLLM routes them to
Anthropic, Ollama, Gemini, OpenAI, or any other supported provider.

```
Harness (Elixir)
  → LiteLLM proxy (Python, localhost:4000)
    → Anthropic API
    → Ollama (local)
    → Gemini API
    → OpenAI API
    → … (100+ providers)
```

Docs: https://docs.litellm.ai/docs/providers/litellm_proxy

---

## Scope

### Phase 1 — Proxy setup + single adapter

- Deploy LiteLLM proxy as a local service (Docker or `pip install litellm`)
- Configure providers in `litellm_config.yaml` (Anthropic, Ollama, Gemini)
- Write a single `Aetheris.Execution.LLMAdapter.LiteLLM` Elixir adapter
  (OpenAI-compatible, hits `localhost:4000`)
- Retire the three existing adapters
- Confirm all existing agent runs work through the proxy

### Phase 2 — Spend tracking

- Enable LiteLLM's spend tracking backend (SQLite or Postgres)
- Tag requests by `run_id` and `use_case` via LiteLLM's metadata headers
- Surface spend data in Rig alongside trajectory token/cost data
- Retire `pricing.ex` — cost comes from LiteLLM, not a local table

### Phase 3 — Cache token pricing

- Enable Anthropic prompt caching in the harness
- Confirm LiteLLM captures `cache_read_input_tokens` and
  `cache_creation_input_tokens` correctly
- Surface cache savings in Rig trajectory view

---

## Key decisions to make at design time

**LiteLLM deployment model.** Options:
- `pip install litellm` + run as a local process alongside the harness
- Docker container (`ghcr.io/berriai/litellm`)
- LiteLLM cloud (managed, adds cost)

For a local dev setup, `pip install litellm` is simplest.

**Adapter rewrite scope.** The current `LLMAdapter` behaviour has a `call/2`
spec that returns a harness-specific response map. The LiteLLM adapter needs
to translate the OpenAI-compatible response back to that shape, or the
response shape itself needs to change. Evaluate whether to keep the existing
response shape (less disruption) or adopt OpenAI shape throughout (cleaner
long term).

**`pricing.ex` retirement timing.** Keep `pricing.ex` until Phase 2 spend
tracking is confirmed working. Don't remove it in Phase 1 — it's the fallback
if LiteLLM spend tracking has gaps.

**Model string mapping.** The harness uses model strings like
`claude-haiku-4-5-20251001`. LiteLLM uses its own model naming convention.
A mapping table or passthrough config will be needed.

---

## What does NOT change

- `event.ex` struct — unchanged
- `llm_responded` event payload fields — `input_tokens`, `output_tokens`,
  `cost_usd` remain; source moves from harness computation to LiteLLM response
- Rig P6 token/cost surface — reads the same fields regardless of where they
  came from
- Agent `.exs` files — no changes needed; LLM adapter is an infrastructure
  concern below the agent level

---

## References

- LiteLLM proxy docs: https://docs.litellm.ai/docs/providers/litellm_proxy
- LiteLLM spend tracking: https://docs.litellm.ai/docs/proxy/cost_tracking
- LiteLLM Anthropic docs: https://docs.litellm.ai/docs/providers/anthropic
- Current adapters: `lib/aetheris/execution/llm_adapter/`
- Current pricing: `lib/aetheris/execution/pricing.ex` (once landed)
