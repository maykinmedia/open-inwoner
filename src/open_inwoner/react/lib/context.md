# Context pattern for composable web components

Web components render in isolated shadow roots — each one is a separate Preact
tree. To share state across that boundary we use the
`@maykinmedia/preact-custom-element` `_preact` event bus, which propagates
Preact context through shadow DOM automatically.

The goal: every component works **standalone** (in Storybook, tests, or plain
HTML) and also works **nested** inside a parent component that owns the shared
state — without the consumer knowing which mode it is in.

---

## File structure

```
ComponentName/
  context.ts                  — interface + unconditional consumer hook
  useComponentNameProvider.ts — all state + bridge logic (the hook)
  ComponentName.tsx           — provides context, renders markup
  ComponentName.scss
  ComponentName.stories.tsx
  constants.ts
```

No `ContextProvider.tsx` file. The component **is** the provider.

---

## The four layers

### 1. `context.ts` — interface + dumb hook

Defines the shape of the local context and exports a hook that reads it. **No
knowledge of parent contexts. No conditional hook calls.**

```ts
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

export const useSelectContext = (): SelectContextValue => {
  const ctx = useContext(SelectContext);
  if (!ctx) throw new Error('useSelectContext must be used within a Select');
  return ctx;
};
```

Rules:

- The hook is always unconditional.
- `context.ts` never imports a parent context.
- The interface only exposes what consumers actually need.

---

### 2. `useComponentNameProvider.ts` — state + bridge hook

All state management and parent-context bridging lives here. **This is the only
file that knows about both contexts.** Keeping it in a hook makes the logic
independently testable and keeps the component file focused on markup.

```ts
export const useSelectProvider = (
  name: string,
  multiple: boolean,
): SelectContextValue & { choices: IFilterChoice[] } => {
  // 1. Read parent context unconditionally — null when standalone.
  const rootCtx = useContext(SignalTestContext);

  // 2. Own local state for standalone mode.
  const ownSelected = useSignal<string[]>([]);
  const choiceMap = useSignal<Record<string, string>>({});

  // 3. Resolve values: parent context wins when present.
  const selectedValues = rootCtx
    ? (rootCtx.selected.value[name] ?? [])
    : ownSelected.value;

  // 4. Bridge: registerChoice writes to local choiceMap AND propagates up.
  const registerChoice = (value: string, label: string, initialSelected = false) => {
    choiceMap.value = { ...choiceMap.value, [value]: label };
    if (rootCtx) rootCtx.registerOption(name, value, label, initialSelected);
    else if (initialSelected) ownSelected.value = [...ownSelected.value, value];
  };

  const toggle = (value: string) => {
    if (rootCtx) rootCtx.toggle(name, value);
    else ownSelected.value = /* xor */ ...;
  };

  // 5. Return the context value + any extra state the component needs to render.
  const choices = Object.entries(choiceMap.value).map(([value, label]) => ({ value, label }));
  return { name, multiple, selectedValues, registerChoice, toggle, choices };
};
```

Rules:

- All `useContext` calls are at the top level — never inside conditions.
- Local signals cover the standalone case.
- The bridge (step 4) is the only place where parent and local state meet.
- Returns the complete `SelectContextValue` so the component just passes it
  straight to the provider.

---

### 3. `ComponentName.tsx` — provides context, renders markup

With all logic extracted into the hook, the component only does two things:
provide the context and render the markup.

```tsx
const Select: AC<SelectProps> = ({
  name,
  multiple = true,
  children,
  ...props
}) => {
  const ctx = useSelectProvider(name, multiple);

  return (
    <SelectContext.Provider value={ctx}>
      {/* markup using ctx.choices, ctx.selectedValues etc. */}
    </SelectContext.Provider>
  );
};
```

Rules:

- No state logic in the component body.
- Children receive the **local** context only; they are unaware of the root.

---

### 4. Consumer components — use the local hook only

```tsx
const SelectOption: AC<OptionProps> = ({ value, label }) => {
  // Only ever reads from the nearest local context.
  const { selectedValues, registerChoice, toggle } = useSelectContext();
  ...
};
```

Rules:

- Consumers call `useSelectContext()` (or whatever local hook).
- Consumers never import or call a root/parent context hook.
- This makes consumers fully reusable and testable in isolation.

---

## Why not put the bridging logic in `context.ts`?

```ts
// ❌ Broken — violates Rules of Hooks
export const useSelectContext = () => {
  const rootCtx = useContext(RootContext);
  const localCtx = rootCtx ? rootCtx : useContext(SelectContext); // conditional!
  ...
};
```

`useContext` is a hook. Hooks must be called unconditionally on every render.
The ternary makes the second `useContext` call conditional, which causes
unpredictable behaviour and errors in strict mode.

---

## Nesting depth

The same pattern composes to any depth:

```
RootContext  (Root.tsx        + useRootProvider.ts)
  └─ SelectContext  (Select.tsx      + useSelectProvider.ts  — bridges from Root)
       └─ OptionContext  (Option.tsx + useOptionProvider.ts  — bridges from Select)
```

Each level provides a narrower, scoped context. Consumers at any level only call
the hook one level up from themselves. Each provider hook is independently
testable with `renderHook` — no DOM or shadow DOM required.

---

## Standalone usage (Storybook / tests)

Because the provider component handles both modes, no mock context or wrapper is
needed in stories:

```tsx
// Works without any provider — Select manages its own state.
<Select name="status" label="Status">
  <SelectOption value="open" label="Open" />
</Select>
```

When the same markup is used inside a root web component, state is automatically
delegated upward via the bridge — no change at the consumer side.
