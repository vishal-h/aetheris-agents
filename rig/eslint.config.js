import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    rules: {
      // Decision record — BL-017 (#68), rejected 2026-07-15 (human call, on
      // claude-ui recommendation). Disabled rule-level, not per-site.
      //
      // Permits: data-fetching hooks that reset state synchronously in an
      // effect, e.g. `useEffect(() => { if (!id) setData(null); ... }, [id])`
      // (28 errors across ~22 hook sites under src/hooks/; count verified in
      // the BL-017 packet — not the ticket's pre-count of "all 31 one rule").
      //
      // Why: these resets are functionally correct — the rule targets render
      // hygiene (cascading re-renders), not bugs. The ~22 sites have no
      // frontend test runner covering them, so refactoring to satisfy the rule
      // is churn with no safety net; the risk outweighs the dev-time benefit.
      //
      // Revisit when: a frontend test runner exists — then the refactor has a
      // net and the rule can be re-enabled and worked through.
      'react-hooks/set-state-in-effect': 'off',
    },
  },
])
