# React Code Style Guide (Recoil + MUI)

This document defines conventions for a **lean, single-repo** React project
using **Recoil** for UI state and **Material UI (MUI)** for components. It
favors **one thing per file**, minimal components, extracted logic, and
dead-simple navigation.

---

## 1) Project Layout (Simple & Flat)

```
src/
  main.tsx
  App.tsx
  theme.ts                 # MUI theme (optional)
  routes.tsx               # if you have routing
  components/              # UI only (tiny, declarative)
    UserMenu/
      UserMenu.tsx
      UserMenu.styles.ts   # styled() or exported sx objects
    LoadingSpinner.tsx
  hooks/                   # app logic lives here
    useFilters.hook.ts
    useDebouncedValue.hook.ts
    useUser.hook.ts
  state/                   # Recoil atoms & selectors only
    user.atom.ts
    filters.atom.ts
    filteredRows.selector.ts
  utils/                   # pure functions, no React
    formatBytes.util.ts
    clamp.util.ts
    assert.util.ts
  services/                # I/O (HTTP, storage, auth)
    http.client.ts
    user.api.ts
  types/                   # shared TypeScript types
    index.ts
```

**Rules**

-   Keep it flat until it hurts. Only add subfolders when you hit the **Rule of
    3** (see §9).
-   File name equals the single thing it exports (e.g., `useFilters.hook.ts` →
    `useFilters`).

---

## 2) File Naming & Suffixes

Use role-based suffixes to make file purpose obvious at a glance:

-   Components: `ComponentName.tsx` (default export)
-   Styles: `ComponentName.styles.ts`
-   Hooks: `useThing.hook.ts`
-   Recoil Atoms: `thing.atom.ts`
-   Recoil Selectors: `thing.selector.ts`
-   Utils (pure): `thing.util.ts`
-   Services (I/O): `thing.api.ts` or `thing.service.ts`
-   Types: `thing.types.ts` (optional), or `types/index.ts`

**One export per file.** Default export for components; named export for
everything else.

---

## 3) Components (Keep Them Tiny)

**Principle:** Components orchestrate view, **not** logic.

**Do**

-   Be declarative: props in → JSX out
-   Defer state/derivations/side-effects to hooks
-   Import styles from `.styles.ts`
-   Accept only the props you actually use
-   Prefer composition over boolean prop explosions

**Avoid**

-   Inline business logic or I/O
-   Multiple responsibilities
-   Coupling to data fetching / timers / subscriptions

---

## 4) Hooks (Brains Live Here)

**Goal:** Make components trivial by extracting logic to hooks.

**Guidelines**

-   One purpose per hook (e.g., `useFilters`, `useAutosave`,
    `useKeyboardShortcuts`)
-   **Return a view model**: `{ state, actions }` (shape results for the UI)
-   **Isolate side-effects** inside hooks (network, timers, subscriptions, DOM
    listeners)
-   Prefer `useReducer` for multi-step logic instead of many `useState`s
-   Keep arguments **plain** (no opaque context objects)
-   Ensure **stable identities** for returned callbacks via `useCallback` when
    consumers care about referential equality
-   Memoize heavy derived values with `useMemo`

**Example**

```ts
// src/hooks/useFilters.hook.ts
import { useRecoilState, useRecoilValue } from "recoil";
import { filtersAtom } from "../state/filters.atom";
import { filteredRowsSelector } from "../state/filteredRows.selector";

export function useFilters() {
    const [filters, setFilters] = useRecoilState(filtersAtom);
    const rows = useRecoilValue(filteredRowsSelector);

    const actions = {
        setText: (text: string) => setFilters((f) => ({ ...f, text })),
        setTags: (tags: string[]) => setFilters((f) => ({ ...f, tags })),
        reset: () => setFilters({ text: "", tags: [] }),
    };

    return { filters, rows, actions };
}
```

---

## 5) Recoil (Small Atoms, Smart Selectors)

**Atoms**

-   Keep atoms small and focused—store **raw** state
-   Namespace keys to avoid collisions: `"user/atom"`, `"filters/atom"`

**Selectors**

-   Put **derivations** in selectors (formatting, joins, filters)
-   Treat selectors like pure functions for easy testing

**Effects**

-   Use `effects_UNSTABLE` for persistence/logging/analytics; keep side effects
    **out** of components

**Example**

```ts
// src/state/filters.atom.ts
import { atom } from "recoil";
export type Filters = { text: string; tags: string[] };
export const filtersAtom = atom<Filters>({
    key: "filters",
    default: { text: "", tags: [] },
});
```

```ts
// src/state/filteredRows.selector.ts
import { selector } from "recoil";
import { filtersAtom } from "./filters.atom";
export const filteredRowsSelector = selector<string[]>({
    key: "filteredRows",
    get: ({ get }) => {
        const { text } = get(filtersAtom);
        const rows = ["alpha", "beta", "gamma"]; // replace with your source
        return rows.filter((r) =>
            r.toLowerCase().includes(text.toLowerCase())
        );
    },
});
```

---

## 6) MUI Styling (Noise-Free Components)

-   Keep design tokens in `theme.ts` (palette, spacing, typography)
-   For reusable styles, prefer `styled()` in `.styles.ts`
-   Use `sx` inline only for truly one-off tweaks
-   Avoid hard-coded colors/sizes in components—pull from theme

**Example**

```ts
// src/components/UserMenu/UserMenu.styles.ts
import { styled, Menu } from "@mui/material";
export const StyledMenu = styled(Menu)(({ theme }) => ({
    "& .MuiPaper-root": { borderRadius: 12, padding: theme.spacing(1) },
}));
```

```tsx
// src/components/UserMenu/UserMenu.tsx
import { StyledMenu } from "./UserMenu.styles";
export default function UserMenu({ anchorEl, onClose }) {
    return (
        <StyledMenu
            open={Boolean(anchorEl)}
            anchorEl={anchorEl}
            onClose={onClose}
        />
    );
}
```

---

## 7) Utils & Services

**Utils (`utils/`)**

-   Pure functions only—no React, no I/O, no globals
-   Deterministic, unit-testable

**Services (`services/`)**

-   I/O modules: HTTP clients, storage, auth
-   No React imports; keep APIs promise-based and composable
-   Keep Recoil/state concerns out of services

---

## 8) Imports & Module Boundaries

-   Relative imports within `src/` are fine; optionally add a single alias
    `"@/*"` → `src/*`
-   Avoid deep relative paths across folders (`../../../`)—introduce an alias
    if needed
-   Use barrel files **sparingly** at folder boundaries when they reduce
    friction

---

## 9) Foldering Heuristic (Rule of 3)

Stay flat until you have **~3** items of the same concern. Then introduce a
folder. Examples:

-   Three or more related hooks → create `hooks/featureX/`
-   Three or more component peers → create `components/FeatureX/`

Avoid premature nesting; it harms discoverability.

---

## 10) Testing

-   **Utils & selectors**: unit-test as pure logic
-   **Hooks**: test behavior via `@testing-library/react`’s `renderHook`
-   **Components**: keep tests minimal—wiring/props/render paths
-   Prefer strict TypeScript and ESLint to prevent whole classes of bugs

**Recommended TS config**

```jsonc
{
    "compilerOptions": {
        "strict": true,
        "exactOptionalPropertyTypes": true,
        "noUncheckedIndexedAccess": true
    }
}
```

---

## 11) Commit & PR Hygiene

-   Keep diffs small: one conceptual change per PR
-   Follow file suffixes and one-export-per-file rule
-   Enforce lint/format on pre-commit (ESLint + Prettier)
-   Add/adjust tests for logic moved into hooks/utils/selectors

---

## 12) Quick Principles Recap

-   **One purpose per file.** File name equals export.
-   **Components are view shells.** Hooks are the brains.
-   **Small atoms, smart selectors.** Derive—don’t duplicate.
-   **Styles near components; tokens in theme.**
-   **Utils are pure; services are I/O.**
-   **Keep it flat until it hurts (Rule of 3).**
