# Context pattern for composable web components

Web components render in isolated shadow roots — each custom element is a
separate Preact tree. Standard Preact context does not cross shadow boundaries
out of the box. The `@maykinmedia/preact-custom-element` library bridges this
via a `_preact` custom event that bubbles through the DOM (including shadow
boundaries). Context provided in a parent shadow root is available to children
registered with this library.

The goal: every component works **standalone** (Storybook, unit tests, plain
HTML) and also works **nested** inside a parent component that owns shared state
— with no change required at the consumer side.

---

## Why signals, not `useState`

React-style `useState` is local to a single Preact tree. A value held in
`useState` inside `oip-filter-root` cannot be read by `oip-filter-option`
because they are in different shadow roots.

`@preact/signals` signals are plain JavaScript objects. They can be placed in
context and passed through the `_preact` event bus as-is. Reading a signal's
`.value` inside any component (in any shadow root) creates a subscription — the
component re-renders automatically when the signal changes, even across shadow
boundaries.

```
                  root shadow root
                 ┌──────────────────────────┐
  selected  ──►  │  Signal<Record<...>>     │  ──► sent via _preact event bus
                 └──────────────────────────┘
                         ↓
                  child shadow root
                 ┌──────────────────────────┐
                 │  reads selected.value    │  ──► re-renders on change ✓
                 └──────────────────────────┘
```

Use `Signal` for mutable state and `ReadonlySignal` (from `useComputed`) for
derived state. Never expose raw signals at the consumer level — expose `.value`
reads or the signal itself only inside provider hooks.

---

## File structure

```
ComponentName/
  context.ts                    — interface + unconditional consumer hook
  useComponentNameProvider.ts   — all state + bridge logic
  ComponentName.tsx             — provides context, renders markup
  ComponentName.scss            — component-level styles
  ComponentName.stories.tsx     — Storybook stories
  constants.ts                  — web component definition (tagName, propNames)
```

No `ComponentNameProvider.tsx` or `ComponentNameContext.tsx`. The component
**is** the provider. The hook **is** the bridge.

---

## The four layers

### 1. `context.ts` — interface and dumb consumer hook

Defines what consumers can read from context. **No knowledge of parent contexts.
No conditional hook calls. No state.**

```ts
import type { Signal, ReadonlySignal } from '@preact/signals';
import { createContext } from 'preact';
import { useContext } from 'preact/hooks';

export interface SelectContextValue {
  name: string;
  multiple: boolean;
  selectedValues: string[];
  registerChoice: (
    value: string,
    label: string,
    initialSelected?: boolean
  ) => void;
  toggle: (value: string) => void;
}

export const SelectContext = createContext<SelectContextValue | null>(null);

// This hook is the only public API for consumers.
// It is always unconditional — no ifs, no parent context checks.
export const useSelectContext = (): SelectContextValue => {
  const ctx = useContext(SelectContext);
  if (!ctx) throw new Error('useSelectContext must be used within a Select');
  return ctx;
};
```

**Rules for `context.ts`:**

- The consumer hook calls `useContext` once, unconditionally.
- It throws a descriptive error when called outside the provider — this is
  intentional: a missing provider is a programming error, not a runtime case.
- The interface exposes only what leaf consumers need. Rendering helpers
  (`choices`, `isOpen`, `containerRef`) belong in the provider hook's return
  type, not here.
- This file never imports a parent or root context.

---

### 2. `useComponentNameProvider.ts` — state and bridge hook

All state management, signal wiring, and parent-context bridging lives here.
**This is the only file that knows about both contexts.** Keeping it in a hook
makes the logic independently testable without mounting a component tree.

```ts
import { useSignal } from '@preact/signals';
import { useContext } from 'preact/hooks';
import { SignalTestContext } from '../NewFilter/context';
import type { SelectContextValue } from './context';

export const useSelectProvider = (
  name: string,
  multiple: boolean
): SelectContextValue & { choices: { value: string; label: string }[] } => {
  // ── Step 1: read parent context unconditionally ──────────────────────────
  // null when standalone (no root ancestor); non-null when nested.
  const rootCtx = useContext(SignalTestContext);

  // ── Step 2: own local signals for standalone mode ────────────────────────
  // These are used only when rootCtx is null.
  const ownSelected = useSignal<string[]>([]);
  const choiceMap = useSignal<Record<string, string>>({});

  // ── Step 3: resolve derived values ───────────────────────────────────────
  // Root context wins when present; own state is the fallback.
  const selectedValues = rootCtx
    ? (rootCtx.selected.value[name] ?? [])
    : ownSelected.value;

  // ── Step 4: bridge actions ────────────────────────────────────────────────
  // Each action delegates upward when nested; operates on local state when not.
  const registerChoice = (
    value: string,
    label: string,
    initialSelected = false
  ) => {
    choiceMap.value = { ...choiceMap.value, [value]: label };
    if (rootCtx) {
      rootCtx.registerOption(name, value, label, initialSelected);
    } else if (initialSelected) {
      ownSelected.value = [...ownSelected.value, value];
    }
  };

  const toggle = (value: string) => {
    if (rootCtx) {
      multiple ? rootCtx.toggle(name, value) : rootCtx.toggleRadio(name, value);
      return;
    }
    if (multiple) {
      ownSelected.value = ownSelected.value.includes(value)
        ? ownSelected.value.filter((v) => v !== value)
        : [...ownSelected.value, value];
    } else {
      ownSelected.value = [value];
    }
  };

  // ── Step 5: derived state for rendering ───────────────────────────────────
  // choiceMap is a signal, so this array updates reactively as options mount.
  const choices = Object.entries(choiceMap.value).map(([value, label]) => ({
    value,
    label,
  }));

  return { name, multiple, selectedValues, registerChoice, toggle, choices };
};
```

**Rules for `useXxxProvider.ts`:**

- All `useContext` / `useSignal` / `useComputed` calls are at the **top level**,
  never inside conditions, loops, or callbacks.
- Local signals exist for every piece of state the root context provides. The
  component must function without a root context.
- The "root context wins" pattern (step 3) means the standalone signals are
  never written when a root context is present — there is one source of truth.
- Signal mutations must replace the whole value
  (`signal.value = { ...old, key: val }`) because signals use reference
  equality. Mutating a nested object won't trigger subscribers.
- The return type extends `SelectContextValue` with rendering extras. Anything
  only needed by the component (e.g. `isOpen`, `containerRef`) is added here,
  not to `SelectContextValue`.

---

### 3. `ComponentName.tsx` — provides context, renders markup

With all logic in the hook, the component does exactly two things: call the hook
and provide the context.

```tsx
import { type AnyComponent as AC } from 'preact';
import { SelectContext } from './context';
import { useSelectProvider } from './useSelectProvider';

const Select: AC<SelectProps> = ({ name, multiple = true, children }) => {
  const { choices, isOpen, ...ctx } = useSelectProvider(name, multiple);

  return (
    <SelectContext.Provider value={ctx}>
      {/* render using choices, isOpen, ctx.selectedValues, etc. */}
    </SelectContext.Provider>
  );
};
```

**Rules for `ComponentName.tsx`:**

- No `useSignal`, `useState`, or `useContext` calls in the component body — all
  state comes from the provider hook.
- The component is the provider: it wraps children with `<XxxContext.Provider>`.
- Children (including deeply nested ones across shadow roots) will receive the
  local context via the `_preact` event bus automatically.
- The component does not know or care whether it is nested inside a root context
  or standing alone.

---

### 4. Consumers — use the local hook only

```tsx
import { useSelectContext } from './context';

const SelectOption: AC<OptionProps> = ({ value, label, initialSelected }) => {
  const { selectedValues, registerChoice, toggle } = useSelectContext();

  useEffect(() => {
    registerChoice(value, label, initialSelected);
  }, []);

  const checked = selectedValues.includes(value);

  return (
    <label>
      <input type="checkbox" checked={checked} onChange={() => toggle(value)} />
      {label}
    </label>
  );
};
```

**Rules for consumers:**

- Call only the local hook (`useSelectContext`, `useChipsContext`, etc.).
- Never import or call a root/parent context hook (`useSignalTest`, etc.).
- The consumer is unaware of whether state is owned locally or delegated upward.
  This makes it fully reusable and testable in isolation.

---

## Anti-patterns and why they break

### Conditional `useContext` — violates Rules of Hooks

```ts
// ❌ Broken
export const useSelectContext = () => {
  const rootCtx = useContext(RootContext);
  // The second useContext is conditional — React/Preact will throw in strict mode
  // and produce unpredictable behaviour otherwise.
  const localCtx = rootCtx ? rootCtx : useContext(SelectContext);
  return localCtx;
};
```

Hooks must be called in the same order on every render. A ternary that skips
`useContext` on some renders corrupts the hook call index. Fix: always call both
`useContext` calls unconditionally, then choose between the results.

---

### Bridging in `context.ts` — wrong layer

```ts
// ❌ Wrong layer — context.ts should not know about parent contexts
import { SignalTestContext } from '../NewFilter/context';

export const useSelectContext = () => {
  const rootCtx = useContext(SignalTestContext); // parent concern
  const localCtx = useContext(SelectContext);
  return rootCtx ?? localCtx;
};
```

This couples the consumer hook to a specific parent, preventing reuse in other
trees and making the abstraction leaky. All bridging belongs in
`useXxxProvider.ts`.

---

### Shadow DOM `contains()` — fails for slotted content

```ts
// ❌ Broken inside shadow DOM
document.addEventListener('mousedown', (e) => {
  if (!ref.current.contains(e.target as Node)) onClickOutside();
});
```

When a click originates inside a shadow root, the browser retargets `e.target`
to the shadow host element for outside listeners. `contains()` sees the host
element, not the actual target, and returns the wrong answer.

```ts
// ✓ Correct — composedPath() contains the full chain across shadow boundaries
document.addEventListener('mousedown', (e) => {
  if (!e.composedPath().includes(ref.current)) onClickOutside();
});
```

---

### `always-open` vs `alwaysOpen` in `cloneElement`

Custom elements register props via `observedAttributes` using the camelCase
names from `propNames`. When Preact renders a custom element, it sets props via
JavaScript property setters (camelCase), not via `setAttribute`.

```tsx
// ❌ `always-open` attribute is never picked up — prop stays undefined
cloneElement(child, { 'always-open': true });

// ✓ Preact maps camelCase to the JS property setter
cloneElement(child, { alwaysOpen: true });
```

In plain HTML templates use the kebab-case attribute (`always-open="true"`); in
JSX / `cloneElement` use the camelCase prop name (`alwaysOpen`).

---

### Mutating signal values in place

```ts
// ❌ Mutation — subscribers do not fire
signal.value.someKey = 'new-value';

// ✓ Replace — creates a new reference, subscribers fire
signal.value = { ...signal.value, someKey: 'new-value' };
```

---

## Web component definition (`constants.ts`)

Each component that is exposed as a custom element needs a definition:

```ts
import { createStyleSheets } from '@react/lib/css';
import type { WebComponentDefinition } from '@react/lib/web-component';
import selectStyle from './Select.scss?inline';
import type { SelectProps } from './Select';

export const SELECT_DEFINITION: WebComponentDefinition<
  'oip-sig-list-test',
  SelectProps
> = {
  tagName: 'oip-sig-list-test',
  // propNames drives observedAttributes — must match SelectProps exactly.
  propNames: ['name', 'label', 'alwaysOpen', 'multiple'],
  options: {
    shadow: true,
    adoptedStyleSheets: createStyleSheets(selectStyle),
  },
  importer: () => import('./Select'),
};
```

`adoptedStyleSheets` injects the compiled SCSS into the shadow root via
`CSSStyleSheet.replace()`. Import the SCSS file with `?inline` (Vite) to get the
raw string. Each component brings its own style sheet; there is no global
cascade into shadow roots.

`propNames` and `SelectProps` must stay in sync. A prop missing from `propNames`
will not be observed as an attribute and will not update when the HTML attribute
changes.

---

## Standalone usage (Storybook / tests)

No mock context or wrapper is needed:

```tsx
// Works without any provider — Select owns its own signal state.
<Select name="status" label="Status">
  <SelectOption value="open" label="Open" />
  <SelectOption value="closed" label="Closed" />
</Select>
```

When a root context is present (e.g. `oip-sig-root-test` ancestor), state is
automatically delegated upward through the bridge.

For components that render nothing when standalone (e.g. `Chips`, which hides
when nothing is selected), provide a lightweight `SignalTestContext` mock in the
story:

```tsx
export const WithSelection: Story = {
  render: () => {
    const selected = useSignal({ status: ['open'] });
    const isFiltered = useComputed(() => true);
    const isDirty = useComputed(() => false);
    return (
      <SignalTestContext.Provider
        value={{
          selected,
          isFiltered,
          isDirty,
          optionLabels: { status: { open: 'Open' } },
          toggle: () => {},
          toggleRadio: () => {},
          registerOption: () => {},
          clearAll: () => {},
          applyFilters: () => {},
        }}
      >
        <Chips />
      </SignalTestContext.Provider>
    );
  },
};
```

---

## Testing strategy

| Layer                     | Test type        | What to test                                           |
| ------------------------- | ---------------- | ------------------------------------------------------ |
| `context.ts`              | Unit             | Hook throws when called outside provider               |
| `useXxxProvider.ts`       | `renderHook`     | State transitions, bridge delegation, no-root fallback |
| `ComponentName.tsx`       | Component test   | Renders correct markup, provides context               |
| Consumer (`SelectOption`) | Component test   | Registration, checked state, toggle interaction        |
| Full tree                 | Integration test | Root context + Select + Option end-to-end              |

Use `renderHook` from `@testing-library/preact` to test provider hooks in
isolation — no shadow DOM or custom element registration required:

```ts
it('falls back to own state when standalone', () => {
  const { result } = renderHook(() => useSelectProvider('status', true));
  act(() => result.current.registerChoice('open', 'Open', true));
  expect(result.current.selectedValues).toEqual(['open']);
});

it('delegates to root context when present', () => {
  const toggle = vi.fn();
  const wrapper = ({ children }) => (
    <SignalTestContext.Provider value={{ ...mockRootCtx, toggle }}>
      {children}
    </SignalTestContext.Provider>
  );
  const { result } = renderHook(() => useSelectProvider('status', true), { wrapper });
  act(() => result.current.toggle('open'));
  expect(toggle).toHaveBeenCalledWith('status', 'open');
});
```

---

## Nesting depth

The pattern composes to any depth. Each level provides a narrower, scoped
context. Each provider hook only bridges one level up:

```
SignalTestContext  (Root.tsx        + useRootProvider.ts)
  └─ SelectContext  (Select.tsx     + useSelectProvider.ts  — bridges from Root)
       └─ OptionContext  (Option.tsx + useOptionProvider.ts — bridges from Select)
```

Consumers at any level call only the hook one level up from themselves.

---

## Checklist: adding a new component

1. **`context.ts`** — define the interface; write the unconditional consumer
   hook; no parent context imports.
2. **`useComponentNameProvider.ts`** — read parent context unconditionally at
   the top; define own signals for every piece of state; bridge each action;
   return the complete context value plus render extras.
3. **`ComponentName.tsx`** — call the hook; wrap output with
   `<XxxContext.Provider value={ctx}>`; no state logic.
4. **`constants.ts`** — define the web component; list all props in `propNames`;
   wire `adoptedStyleSheets`.
5. **Consumer components** — call only the local `useXxxContext()` hook; no root
   context imports.
6. **Stories** — one standalone story (no wrapper needed for components with
   visible default state); one nested story (inside a root context mock) if the
   component requires pre-populated state to be visible.
