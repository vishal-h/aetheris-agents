/**
 * Which plan-card hint values may be rendered in clear (BL-095).
 *
 * `StepCard` used to print `KEY: value` for every set hint key, so an approved payslip plan
 * displayed `SMTP_PASSWORD` and the service-account path in cleartext.
 *
 * **Deny by default, not mask-if-flagged.** The rule is "show only what is *known* safe",
 * never "hide what is *known* secret". That distinction is load-bearing here rather than
 * stylistic — enumerating the 15 hint keys against their metadata found:
 *
 *   - only `SMTP_PASSWORD` carries `masked: true`;
 *   - `DOCBUILDER_CONTEXT_FILE` and `DOCBUILDER_REQUEST` have **no metadata at all** (they
 *     are hint-only, absent from AGENT_CONFIG_DEFS), so a mask-if-flagged rule would print
 *     whatever they hold;
 *   - a future hint key added without a def would leak by default under that rule.
 *
 * Deny-by-default makes the safe direction the automatic one: an unknown key shows its
 * status, never its value. The cost is a key that is genuinely safe but undeclared shows as
 * "set" until someone declares it — a visible, harmless prompt to add the metadata.
 *
 * **Source of truth is `AGENT_CONFIG_DEFS` alone**, deliberately narrower than
 * "defs ∪ manifest env_deps". No hint key is reachable only via a manifest today (verified
 * across every committed `tools.json`), so unioning in `env_deps` buys nothing now and would
 * require pulling the whole tools inventory into this view. It can only ever *widen* what is
 * shown, so omitting it is the conservative direction: a manifest-only hint key renders as
 * "set" rather than in clear.
 */
import { AGENT_CONFIG_DEFS } from '../settings/agentConfigDefs';

/** key → masked. Absent key means "no metadata", which is treated as unsafe. */
export type MaskedMap = ReadonlyMap<string, boolean>;

export function buildMaskedMap(
  defs: ReadonlyArray<{ key: string; masked: boolean }> = AGENT_CONFIG_DEFS,
): MaskedMap {
  return new Map(defs.map((d) => [d.key, d.masked]));
}

/**
 * True only when the key is *explicitly* declared non-secret.
 *
 * `masked === true` → hide. Key absent (no metadata) → hide. Anything else → hide.
 * The single showing branch is an explicit `masked === false`.
 */
export function shouldShowValue(key: string, masked: MaskedMap): boolean {
  return masked.get(key) === false;
}

/**
 * The line rendered for one hint key: the value when known-safe, its status otherwise.
 *
 * "set" rather than omitting the row entirely — that a credential *is* configured is the
 * useful part of the signal on a plan card, and it leaks nothing.
 */
export function hintLine(key: string, value: string, masked: MaskedMap): string {
  return shouldShowValue(key, masked) ? `${key}: ${value}` : `${key}: set`;
}
