# Milestone: v0.1 — App Shell

## Milestone Description
Builds the complete Rig application shell — top bar, sidebar, main content area, and right panel — wired together with routing and a module registry. No Rust backend changes. All tickets are frontend only. At the end of this milestone, Rig should display a fully functional shell with the F2 module listed in the sidebar and placeholder views per section.

## Metadata
- **Repo:** swiftekin/hai-rig
- **Milestone:** v0.1 — App Shell
- **Labels to create before importing:** `shell`, `frontend`, `f2`, `dx`

---
---

## TICKET-01: Base styles and CSS variables

**Labels:** `shell`, `frontend`, `dx`
**Depends on:** none

### Summary
Replace the Vite default styles in `src/index.css` with Rig's base styles, CSS custom properties for theming (light and dark), and typography defaults.

### Context
The scaffold was created with Vite's default CSS. Before building any components we need a clean style foundation with CSS variables that all components will reference. Theming (light/dark) is driven by a `data-theme` attribute on the `<html>` element. See ARCHITECTURE.md — Theming section.

### Scope
**Modify:**
- `src/index.css`

**No other files should be touched.**

### Acceptance Criteria
- [ ] `src/index.css` starts with `@import "tailwindcss";`
- [ ] CSS custom properties defined for both `:root` (light) and `[data-theme="dark"]`
- [ ] Variables cover: background, foreground, sidebar background, sidebar foreground, border, accent, muted, card, ring
- [ ] Base body styles set: font-family (system-ui or Geist if available), font-size, line-height, background, foreground
- [ ] No Vite default styles remain
- [ ] App still compiles and window opens with `cargo tauri dev`

### Agentic Instructions
**Follow:**
- Use CSS custom properties (`--variable-name`) not Tailwind config for theme tokens
- The `data-theme="dark"` attribute approach — not `prefers-color-scheme` media query (user controls theme manually)
- shadcn/ui Nova preset variables are already partially set by shadcn init — extend them, don't replace them
- Keep it minimal — only variables that will actually be used

**Do not:**
- Add JavaScript to this ticket
- Modify `index.html`
- Add any component files
- Use `@apply` — plain CSS variables only in this file

### References
- [ARCHITECTURE.md — Theming](docs/architecture.md)
- [CLAUDE.md](CLAUDE.md)

---
---

## TICKET-02: AppContext — app-wide state

**Labels:** `shell`, `frontend`
**Depends on:** TICKET-01

### Summary
Create the React context that holds app-wide state: active module, active sidebar item, right panel visibility, and theme.

### Context
No external state library is used (no Redux, no Zustand). React context is sufficient for Rig's app-level state. This context is consumed by TopBar, Sidebar, MainArea, and RightPanel. See CLAUDE.md — Key Architectural Rules.

### Scope
**Create:**
- `src/context/AppContext.tsx`

**No other files should be touched.**

### Acceptance Criteria
- [ ] `AppContext.tsx` exports `AppProvider` and `useApp` hook
- [ ] Context shape includes:
  - `activeModule: string` — currently selected module id (e.g. `"f2"`)
  - `activeSidebarItem: string` — currently selected sidebar item id (e.g. `"f2-operations"`)
  - `rightPanelOpen: boolean`
  - `theme: "light" | "dark" | "system"`
  - Setters for each
- [ ] `AppProvider` applies `data-theme` attribute to `document.documentElement` when theme changes
- [ ] `useApp` throws a helpful error if used outside `AppProvider`
- [ ] TypeScript — no `any` types
- [ ] File compiles without errors

### Agentic Instructions
**Follow:**
- `useReducer` pattern preferred over multiple `useState` calls for the context state
- Export types: `AppState`, `AppAction` alongside the context
- Default theme: `"system"` — reads `prefers-color-scheme` on init to set the actual value

**Do not:**
- Import anything from Tauri in this file
- Add persistence logic (localStorage or DuckDB) — that comes later
- Create any UI components in this ticket

### References
- [CLAUDE.md](CLAUDE.md)

---
---

## TICKET-03: Module registry

**Labels:** `shell`, `frontend`, `f2`
**Depends on:** TICKET-02

### Summary
Create the frontend module registry that defines all modules available in Rig, their sidebar structure, and their routes.

### Context
The module registry is the single place where modules are registered in the frontend. The sidebar reads from it. The router reads from it. Adding a new module in future means adding one entry here. See ARCHITECTURE.md — Module System and CLAUDE.md — Adding a New Module.

### Scope
**Create:**
- `src/modules/registry.ts`
- `src/modules/types.ts`

**No other files should be touched.**

### Acceptance Criteria
- [ ] `types.ts` exports:
  - `SidebarItem` type: `{ id: string, label: string, icon: string, path: string }`
  - `Module` type: `{ id: string, label: string, icon: string, sections: SidebarItem[] }`
- [ ] `registry.ts` exports a `modules: Module[]` array
- [ ] F2 module registered with:
  - id: `"f2"`
  - label: `"F2"`
  - Two sections: `{ id: "f2-operations", label: "Operations", path: "/f2/operations" }` and `{ id: "f2-viewer", label: "Viewer", path: "/f2/viewer" }`
  - Icons from `lucide-react`: `FolderSearch` for the module, `ScanSearch` for Operations, `LayoutTree` for Viewer
- [ ] TypeScript — no `any` types
- [ ] Files compile without errors

### Agentic Instructions
**Follow:**
- Icon values should be the component name as a string (e.g. `"FolderSearch"`) — the Sidebar component will resolve them. Do not import lucide components here
- Keep `registry.ts` as pure data — no React, no JSX
- Design should obviously support adding a second module by appending to the array

**Do not:**
- Create any UI components
- Import React
- Add routing logic here — that belongs in App.tsx

### References
- [ARCHITECTURE.md — Module System](docs/architecture.md)
- [CLAUDE.md](CLAUDE.md)

---
---

## TICKET-04: TopBar component

**Labels:** `shell`, `frontend`
**Depends on:** TICKET-02, TICKET-03

### Summary
Build the TopBar component — the fixed top bar showing the app name, a sync button, and a settings button.

### Context
TopBar is always visible regardless of active module. The sync button is delegated to the active module — it calls whatever sync handler the current module has registered. Settings opens a route (not a modal). See SPECS.md — Part 1, Section 1.1.

### Scope
**Create:**
- `src/components/shell/TopBar.tsx`

**No other files should be touched.**

### Acceptance Criteria
- [ ] Fixed top bar, full width, height 48px (`h-12`)
- [ ] Left: app icon (use `Wrench` from lucide-react) + text "Rig"
- [ ] Right: sync button (`RefreshCw` icon) + settings button (`Settings` icon)
- [ ] Sync button shows a spinner (`Loader2` with `animate-spin`) when `syncing` prop is true
- [ ] Sync button is visually disabled (not hidden) when `onSync` prop is not provided
- [ ] Settings button navigates to `/settings` using react-router-dom `useNavigate`
- [ ] Component accepts props: `onSync?: () => void`, `syncing?: boolean`
- [ ] Uses `useApp()` from AppContext — no direct state
- [ ] Responsive to light/dark theme via CSS variables
- [ ] TypeScript — no `any`, props typed with an interface
- [ ] Renders without errors

### Agentic Instructions
**Follow:**
- Use shadcn `Button` component with `variant="ghost"` and `size="icon"` for icon buttons
- Tailwind utility classes for layout — no inline styles
- Keep it simple — no dropdown menus, no complex logic in this ticket

**Do not:**
- Implement the settings panel/route in this ticket
- Add global search (deferred to post-MVP)
- Add any notification or status indicators in this ticket

### References
- [SPECS.md — TopBar](docs/specs.md)
- [CLAUDE.md](CLAUDE.md)

---
---

## TICKET-05: Sidebar component

**Labels:** `shell`, `frontend`
**Depends on:** TICKET-03, TICKET-04

### Summary
Build the Sidebar component — fixed left panel with collapsible module sections and active item highlighting, driven by the module registry.

### Context
The sidebar reads from the module registry and renders each module as a collapsible section with its sub-items listed beneath. Clicking a sub-item navigates to its route and updates AppContext. See SPECS.md — Part 1, Section 1.2.

### Scope
**Create:**
- `src/components/shell/Sidebar.tsx`

**No other files should be touched.**

### Acceptance Criteria
- [ ] Fixed left panel, width 240px (`w-60`)
- [ ] Renders all modules from `registry.ts` as collapsible sections
- [ ] Each section header shows module icon + label + chevron (rotates when expanded)
- [ ] Each section is expanded by default
- [ ] Sub-items show icon + label
- [ ] Clicking a sub-item: updates `activeSidebarItem` in AppContext, navigates to item's path via react-router-dom
- [ ] Active sub-item has distinct visual style (accent background, full-weight text)
- [ ] Hover state on sub-items
- [ ] Bottom of sidebar: a disabled `+ Module` entry with `Plus` icon (no action, placeholder)
- [ ] Divider line between modules and the `+ Module` entry
- [ ] Responsive to light/dark theme
- [ ] TypeScript — no `any`

### Agentic Instructions
**Follow:**
- Use `useNavigate` and `useLocation` from react-router-dom to set and detect active route
- Derive active state from current URL path, not just AppContext — so refresh works correctly
- Icon resolution: registry stores icon names as strings. Sidebar should maintain a local map of `{ [name: string]: LucideIcon }` to resolve them
- Collapsible state managed with local `useState` per section — not in AppContext

**Do not:**
- Make the sidebar resizable in this ticket
- Add a sidebar collapse/hide toggle
- Add any search or filter within the sidebar

### References
- [SPECS.md — Sidebar](docs/specs.md)
- [CLAUDE.md](CLAUDE.md)

---
---

## TICKET-06: RightPanel component

**Labels:** `shell`, `frontend`
**Depends on:** TICKET-02

### Summary
Build the RightPanel component — the optional contextual panel on the right edge that modules can use to show detail views.

### Context
The right panel is hidden by default and toggled by module logic. It has a close button. When open, the main content area reflows — it does not overlay. It renders whatever children are passed to it. See SPECS.md — Part 1, Section 1.4.

### Scope
**Create:**
- `src/components/shell/RightPanel.tsx`

**No other files should be touched.**

### Acceptance Criteria
- [ ] Panel width 320px (`w-80`), sits on the right edge of the main area
- [ ] Visibility driven by `rightPanelOpen` from AppContext
- [ ] When closed: not rendered (or `hidden`) — main content fills the space
- [ ] When open: panel slides in or appears (CSS transition preferred)
- [ ] Header row: title (passed as prop) + close button (`X` icon) that sets `rightPanelOpen = false` in AppContext
- [ ] Body: renders `children` prop
- [ ] Border-left separating it from main content
- [ ] Responsive to light/dark theme
- [ ] Props: `title?: string`, `children: React.ReactNode`
- [ ] TypeScript — no `any`

### Agentic Instructions
**Follow:**
- Use CSS transition for open/close: `transition-all duration-200` — subtle, not flashy
- Panel is part of the layout flow (not `position: fixed` or overlay)
- Close button uses shadcn `Button` with `variant="ghost"` and `size="icon"`

**Do not:**
- Add any F2-specific content in this component — it renders children only
- Add resize functionality

### References
- [SPECS.md — Right Panel](docs/specs.md)
- [CLAUDE.md](CLAUDE.md)

---
---

## TICKET-07: MainArea component with tabs

**Labels:** `shell`, `frontend`
**Depends on:** TICKET-02, TICKET-05

### Summary
Build the MainArea component — the tabbed content area that fills the space between the sidebar and optional right panel. Tabs are defined per route/module.

### Context
Each sidebar item maps to a set of tabs. The MainArea renders the tab strip and the active tab content. Tab definitions come from the active module/route — not hardcoded. At this stage it renders placeholder content per tab. See SPECS.md — Part 1, Section 1.3.

### Scope
**Create:**
- `src/components/shell/MainArea.tsx`
- `src/components/shell/TabBar.tsx`

**No other files should be touched.**

### Acceptance Criteria
- [ ] `MainArea` fills remaining horizontal space (flex-1) and full height
- [ ] Accepts prop: `tabs: Tab[]` where `Tab = { id: string, label: string, content: React.ReactNode }`
- [ ] `TabBar` renders a horizontal strip of tab buttons at the top
- [ ] Active tab highlighted, clickable
- [ ] Active tab content rendered below the tab bar
- [ ] Tab state managed with local `useState` — resets to first tab when `tabs` prop changes
- [ ] If `tabs` is empty or undefined: renders a centred empty state message "Select an item from the sidebar"
- [ ] Responsive to light/dark theme
- [ ] TypeScript — no `any`

### Agentic Instructions
**Follow:**
- Use shadcn `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent` components — install via `bunx shadcn@latest add tabs`
- `TabBar` is a separate component but used only by `MainArea` — keep them in the shell directory
- Tab content area should be scrollable (`overflow-y-auto`) independently of the tab bar

**Do not:**
- Make tabs closable by the user
- Add dynamic tab creation
- Hardcode any F2 tab names here

### References
- [SPECS.md — Main Content Area](docs/specs.md)
- [CLAUDE.md](CLAUDE.md)

---
---

## TICKET-08: F2 placeholder views

**Labels:** `f2`, `frontend`
**Depends on:** TICKET-07

### Summary
Create placeholder view components for both F2 sub-sections (Operations and Viewer), each with their correct tab structure but empty/placeholder content.

### Context
The F2 module has two sidebar items — Operations (F2O) and Viewer (F2V). Each has its own tabs. This ticket creates the shell of those views with placeholder content so the full navigation flow works end to end. Real content comes in later milestones. See SPECS.md — Part 2.

### Scope
**Create:**
- `src/components/modules/f2/F2Operations.tsx`
- `src/components/modules/f2/F2Viewer.tsx`
- `src/components/modules/f2/index.ts`

**No other files should be touched.**

### Acceptance Criteria
- [ ] `F2Operations.tsx` renders two tabs: `Duplicates` and `Index`
  - Each tab shows a placeholder: icon + "Coming soon" or descriptive empty state text
  - Duplicates placeholder: `ScanSearch` icon + "No duplicates found. Add a watched folder to get started."
  - Index placeholder: `Database` icon + "No files indexed yet."
- [ ] `F2Viewer.tsx` renders two tabs: `Views` and `Labels`
  - Views placeholder: `LayoutTree` icon + "No views yet. Files will appear here once indexed."
  - Labels placeholder: `Tag` icon + "No labels applied yet."
- [ ] Both components export as named exports
- [ ] `index.ts` re-exports both components
- [ ] All icons from `lucide-react`
- [ ] Responsive to light/dark theme
- [ ] TypeScript — no `any`

### Agentic Instructions
**Follow:**
- Placeholder content should be centred vertically and horizontally in the tab content area
- Use muted text color (`text-muted-foreground`) for placeholder text
- Keep these components thin — no state, no data fetching, no Tauri calls

**Do not:**
- Add any real data fetching or Tauri invoke calls
- Create DuckDB schema or Rust commands in this ticket
- Add more than the specified tabs

### References
- [SPECS.md — F2 Module](docs/specs.md)
- [CLAUDE.md](CLAUDE.md)

---
---

## TICKET-09: App root layout and routing

**Labels:** `shell`, `frontend`
**Depends on:** TICKET-04, TICKET-05, TICKET-06, TICKET-07, TICKET-08

### Summary
Wire all shell components together in `App.tsx` with react-router-dom routing. The result should be a fully navigable Rig shell with F2 in the sidebar and working tab views.

### Context
This is the integration ticket that assembles the shell. `App.tsx` composes TopBar, Sidebar, MainArea, and RightPanel into the final layout. Routes map sidebar paths to the correct view components. See ARCHITECTURE.md — App Shell Layout.

### Scope
**Modify:**
- `src/App.tsx`
- `src/main.tsx`

**No other files should be touched.**

### Acceptance Criteria
- [ ] `main.tsx` wraps the app in `AppProvider` and `BrowserRouter`
- [ ] `App.tsx` layout:
  - Full viewport height (`h-screen`) flex column
  - TopBar at top (fixed height)
  - Below: flex row containing Sidebar (fixed width) + content area (flex-1)
  - Content area: flex row containing MainArea (flex-1) + RightPanel (conditional)
- [ ] Routes defined:
  - `/` → redirect to `/f2/operations`
  - `/f2/operations` → `F2Operations` component in MainArea
  - `/f2/viewer` → `F2Viewer` component in MainArea
  - `/settings` → placeholder `<div>Settings coming soon</div>`
- [ ] Sidebar active state reflects current route on load and navigation
- [ ] TopBar sync button wired — for now calls `console.log("sync")` as placeholder
- [ ] No layout overflow or scrollbar on the shell itself (only content areas scroll internally)
- [ ] Light and dark theme switching works via AppContext
- [ ] TypeScript — no `any`

### Agentic Instructions
**Follow:**
- Use `<Routes>` and `<Route>` from react-router-dom v6
- Use `<Navigate>` for the root redirect
- `MemoryRouter` is preferred over `BrowserRouter` for Tauri desktop apps — use `MemoryRouter` in `main.tsx`
- Pass tab definitions to `MainArea` from the route level — each route component provides its own tabs

**Do not:**
- Use `HashRouter`
- Implement the settings panel in this ticket — placeholder div is sufficient
- Add any Tauri invoke calls

### References
- [ARCHITECTURE.md — App Shell Layout](docs/architecture.md)
- [SPECS.md — Part 1](docs/specs.md)
- [CLAUDE.md](CLAUDE.md)

---
---

## TICKET-10: Shell visual QA and dark mode

**Labels:** `shell`, `frontend`, `dx`
**Depends on:** TICKET-09

### Summary
Visual quality pass on the assembled shell. Fix any layout issues, verify dark mode works correctly across all components, and ensure consistent use of design tokens.

### Context
After wiring everything together in TICKET-09 there will likely be minor visual inconsistencies — hardcoded colours, missing dark variants, layout gaps. This ticket is a focused cleanup pass before moving to the next milestone.

### Scope
**Modify (as needed):**
- `src/index.css`
- `src/components/shell/TopBar.tsx`
- `src/components/shell/Sidebar.tsx`
- `src/components/shell/MainArea.tsx`
- `src/components/shell/RightPanel.tsx`
- `src/components/shell/TabBar.tsx`
- `src/components/modules/f2/F2Operations.tsx`
- `src/components/modules/f2/F2Viewer.tsx`

**Do not create new files.**

### Acceptance Criteria
- [ ] No hardcoded colour values (`#fff`, `rgb(...)`, named colours) — all via CSS variables or Tailwind semantic classes
- [ ] Dark mode: toggle theme to dark (via AppContext) — all surfaces use dark variants correctly
- [ ] Light mode: toggle back — no artefacts
- [ ] Sidebar active item clearly distinguishable from inactive in both themes
- [ ] TopBar has a visible bottom border separating it from content in both themes
- [ ] Sidebar has a visible right border in both themes
- [ ] No horizontal scrollbar on the shell
- [ ] No content clipped or overflowing outside its container
- [ ] Placeholder views are centred and readable in both themes
- [ ] RightPanel: open it (set `rightPanelOpen = true` in context), verify it appears and MainArea reflows
- [ ] Tab bar and active tab clearly visible in both themes

### Agentic Instructions
**Follow:**
- Use Tailwind semantic classes (`bg-background`, `text-foreground`, `border-border`, `text-muted-foreground`) — these map to CSS variables and handle dark mode automatically
- If a visual fix requires more than 5 lines in a component, add a comment explaining why

**Do not:**
- Add new features or components
- Change routing
- Add any Tauri or data layer code
- Introduce new dependencies

### References
- [SPECS.md — Part 1](docs/specs.md)
- [CLAUDE.md](CLAUDE.md)