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
`useState` inside `oip-form` cannot be read by `oip-select` because they are in
different shadow roots.

`@preact/signals` signals are plain JavaScript objects. They can be placed in
context and passed through the `_preact` event bus as-is. Reading a signal's
`.value` inside any component (in any shadow root) creates a subscription — the
component re-renders automatically when the signal changes, even across shadow
boundaries.

```
                  root shadow root
                 ┌──────────────────────────┐
  values    ──►  │  Signal<Record<...>>     │  ──► sent via _preact event bus
                 └──────────────────────────┘
                         ↓
                  child shadow root
                 ┌──────────────────────────┐
                 │  reads values.value      │  ──► re-renders on change ✓
                 └──────────────────────────┘
```

Use `Signal` for mutable state and `ReadonlySignal` (from `useComputed`) for
derived state. Never expose raw signals at the consumer level — expose `.value`
reads or the signal itself only inside provider hooks.

---

## File structure

```
ComponentName/
  context.ts                    — interface + consumer hooks (nullable + throwing)
  ComponentName.tsx             — state, context provider, markup
  ComponentName.scss            — component-level styles
  ComponentName.stories.tsx     — Storybook stories
  constants.ts                  — web component definition (tagName, propNames)
```

For components with substantial state, logic can be extracted to a
`useComponentNameProvider.ts` hook to keep the component body clean and make the
logic independently testable via `renderHook`. For simpler components, inlining
state directly in the component body is fine.

No `ComponentNameProvider.tsx` or `ComponentNameContext.tsx`. The component
**is** the provider. The hook (when it exists) **is** the bridge.

---

## The layers

### 1. `context.ts` — interface and consumer hooks

Defines what consumers can read from context. **No knowledge of parent contexts.
No conditional hook calls. No state.**

```ts
import { createContext } from 'preact';
import { useContext } from 'preact/hooks';

export interface FilterContextValue {
  registerLabel: (fieldName: string, value: string, label: string) => void;
  getLabel: (fieldName: string, value: string) => string;
  submit: () => void;
}

export const FilterContext = createContext<FilterContextValue | null>(null);

/** Returns the nearest FilterContext value, or `null` if outside oip-filters. */
export const useFilterContext = (): FilterContextValue | null =>
  useContext(FilterContext);

/**
 * Returns the nearest FilterContext value.
 * Throws a descriptive error if called outside an oip-filters tree.
 */
export const useRequiredFilterContext = (): FilterContextValue => {
  const ctx = useContext(FilterContext);
  if (!ctx) throw new Error('Component must be nested inside oip-filters');
  return ctx;
};
```

**Rules for `context.ts`:**

- Export two hooks: a nullable one (`useXxxContext`) for guards and a throwing
  one (`useRequiredXxxContext`) for components that must be nested.
- Both hooks call `useContext` once, unconditionally.
- The throwing variant is intentional: a missing provider is a programming
  error, not a runtime case to handle silently.
- The interface exposes only what leaf consumers need. Rendering helpers
  (`isOpen`, `containerRef`) stay in the component or provider hook, not here.
- This file never imports a parent or sibling context.

---

### 2. `ComponentName.tsx` — state, provider, markup

With all context definitions in `context.ts`, the component owns state and
provides the context. For complex components, state can be extracted to a
`useComponentNameProvider.ts` hook.

```tsx
const Filters = withContextGuard(useFormContext, ({ children }) => {
  const formCtx = useRequiredFormContext();
  const optionLabels = useRef<Record<string, Record<string, string>>>({});

  const registerLabel = (fieldName: string, value: string, label: string) => {
    if (!optionLabels.current[fieldName]) {
      optionLabels.current[fieldName] = {};
    }
    optionLabels.current[fieldName][value] = label;
  };

  const getLabel = (fieldName: string, value: string): string =>
    optionLabels.current[fieldName]?.[value] ?? value;

  const submit = (): void => {
    formCtx.submit((values) => {
      const params = new URLSearchParams();
      Object.entries(values).forEach(([key, vals]) => {
        vals.forEach((v) => params.append(key, v));
      });
      window.location.assign(`${window.location.pathname}?${params}`);
    });
  };

  return (
    <FilterContext.Provider value={{ registerLabel, getLabel, submit }}>
      <div class="oip-filters">{children}</div>
    </FilterContext.Provider>
  );
});
```

**Rules for `ComponentName.tsx`:**

- The component wraps children with `<XxxContext.Provider value={...}>`.
- Children (including deeply nested ones across shadow roots) receive the
  context via the `_preact` event bus automatically.
- The component does not know or care whether it is nested inside a parent
  context or standing alone — `withContextGuard` handles the null case.

---

### 3. Consumers — use the required hook only

```tsx
const SelectOption = withContextGuard(
  useSelectContextNullable,
  ({ value, label }: OptionProps) => {
    const ctx = useSelectContext(); // safe — guard ensures it exists
    const { isSelected, onChange, moveFocus, close, typeahead } =
      ctx.registerOption(value, label);

    return (
      <div
        class="oip-select-option"
        tabIndex={-1}
        onClick={onChange}
        onKeyDown={handleKeyDown}
      >
        <input
          type={ctx.multiple ? 'checkbox' : 'radio'}
          checked={isSelected}
          onChange={onChange}
        />
        <span>{label}</span>
      </div>
    );
  }
);
```

**Rules for consumers:**

- Call only the local required hook (`useRequiredSelectContext`, etc.).
- Never import or call a parent context hook (`useFormContext`, etc.).
- The consumer is unaware of whether state is owned locally or delegated upward.
  This makes it fully reusable and testable in isolation.

---

## withContextGuard

`withContextGuard` is an HOC that guards a component behind a nullable context
check. The wrapped component renders `null` while the context is absent, then
renders normally once context arrives.

This serves two purposes:

1. **Timing**: the `_preact` event propagation is async. There is a window
   between a web component rendering and its parent's context event firing where
   context is `null`. The guard prevents crashes during this window.
2. **Misuse**: renders nothing (dev warning) when the component is used outside
   its required parent — a clear signal of incorrect composition.

```tsx
// Renders null silently while FilterContext is absent.
// Once context arrives the full component renders.
export default withContextGuard(useFilterContext, FormButton);
```

---

## Anti-patterns and why they break

### Conditional `useContext` — violates Rules of Hooks

```ts
// ❌ Broken
export const useSelectContext = () => {
  const rootCtx = useContext(FormContext);
  // The second useContext is conditional — Preact will produce unpredictable behaviour.
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
import { FormContext } from '../Form/context';

export const useSelectContext = () => {
  const formCtx = useContext(FormContext); // parent concern
  const localCtx = useContext(SelectContext);
  return formCtx ?? localCtx;
};
```

This couples the consumer hook to a specific parent, preventing reuse in other
trees and making the abstraction leaky. All bridging belongs in the component
body (or `useXxxProvider.ts` for complex components).

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
  'oip-select',
  SelectProps
> = {
  tagName: 'oip-select',
  // propNames drives observedAttributes — must match SelectProps exactly.
  propNames: ['name', 'label', 'value', 'multiple'],
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

`oip-select` and `oip-select-option` work without any parent context — Select
registers with FormContext when present and manages its own state when not:

```tsx
// Works without oip-form or oip-filters — Select owns its own signal state.
<Select name="status" label="Status">
  <SelectOption value="open" label="Open" />
  <SelectOption value="closed" label="Closed" />
</Select>
```

For components that require parent context to render anything visible (e.g.
`FilterChips` hides when no values are selected), provide a lightweight
`FormContext` mock in the story:

```tsx
export const WithSelection: Story = {
  render: () => {
    const values = useSignal<Record<string, string[]>>({ status: ['open'] });
    const isDirty = useComputed(() => true);
    const isEmpty = useComputed(() => false);
    return (
      <FormContext.Provider
        value={{
          values,
          isDirty,
          isEmpty,
          register: () => ({
            value: computed(() => []),
            setValue: () => {},
            onChange: () => {},
          }),
          removeValue: () => {},
          toggle: () => {},
          submit: () => {},
          reset: () => {},
        }}
      >
        <FilterContext.Provider
          value={{
            registerLabel: () => {},
            getLabel: (_field, value) => value,
            submit: () => {},
          }}
        >
          <FilterChips />
        </FilterContext.Provider>
      </FormContext.Provider>
    );
  },
};
```

---

## Testing strategy

| Layer               | Test type      | What to test                                     |
| ------------------- | -------------- | ------------------------------------------------ |
| `context.ts`        | Unit           | Nullable hook returns null; throwing hook throws |
| `ComponentName.tsx` | Component test | Renders correct markup, provides context         |
| Consumer            | Component test | Registration, checked state, interaction         |
| Full tree           | Integration    | Form + Filters + Select + Option end-to-end      |

Use `renderHook` from `@testing-library/preact` when you extract state to a
provider hook, or mount the component directly when state is inline:

```ts
it('registers a label and returns it', () => {
  const { getByText } = render(
    <FormContext.Provider value={mockFormCtx}>
      <Filters>
        <FilterChips />
        <Select name="status" label="Status">
          <SelectOption value="open" label="Open" />
        </Select>
      </Filters>
    </FormContext.Provider>
  );
  // After mount, SelectOption registers its label via FilterContext.
  // FilterChips should show 'Open', not 'open'.
  expect(getByText('Open')).toBeTruthy();
});
```

---

## Nesting depth

The current filter tree:

```
FormContext    (Form.tsx      — owns all field values, isDirty, isEmpty)
  └─ FilterContext  (Filters.tsx  — label registry, URL navigation, bridges to Form)
       └─ SelectContext  (Select.tsx  — dropdown state, option registration, bridges to Form + Filter)
            └─ (no context)  (SelectOption.tsx  — reads SelectContext only)
```

Consumers at any level call only the hook one level up from themselves.

---

## Checklist: adding a new component

1. **`context.ts`** — define the interface; export a nullable hook and a
   throwing hook; no parent context imports.
2. **`ComponentName.tsx`** — read parent context unconditionally at the top;
   provide the context via `<XxxContext.Provider>`; use `withContextGuard` if
   the component requires a parent context to function.
3. **`constants.ts`** — define the web component; list all props in `propNames`;
   wire `adoptedStyleSheets`.
4. **Consumer components** — call only the local `useRequiredXxxContext()` hook;
   no parent context imports.
5. **Stories** — one standalone story; one story with a parent context mock if
   the component requires pre-populated state to be visible.

---

## HTML composition

Components are composed in HTML templates. There is no domain-specific wrapper
web component — `oip-form` and `oip-filters` are generic and reusable.

Default values are set via the `value` attribute on `oip-select`. Django can
read URL query params server-side and pass them directly:

```html
<oip-form>
  <oip-filters>
    <oip-filter-bar>
      <oip-select
        name="periode"
        label="Periode"
        multiple="false"
        value="{{ request.GET.periode }}"
      >
        {% for year in periode_options %}
        <oip-select-option value="{{ year }}" label="Jaar {{ year }}">
        </oip-select-option>
        {% endfor %}
      </oip-select>

      <oip-select
        name="adres"
        label="Adres"
        value="{{ request.GET.getlist('adres')|join:',' }}"
      >
        {% for address in user.addresses %}
        <oip-select-option value="{{ address }}" label="{{ address }}">
        </oip-select-option>
        {% endfor %}
      </oip-select>

      <oip-form-button>Toon resultaten</oip-form-button>
    </oip-filter-bar>
    <oip-filter-chips></oip-filter-chips>
  </oip-filters>
</oip-form>
```

For multi-select fields with multiple URL params (`?status=open&status=closed`),
join the values as comma-separated for the `value` attribute.
