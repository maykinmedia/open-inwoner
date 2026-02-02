# Future of OIP and Preact Custom Elements.

Currently with the `PCE` (preact-custom-elements) implementation it is not
possible to attach `ElementInternals` to a web-component.

## What are ElementInternals

Element Internals can be used to assign accessibility attributes to a web
component (eg. role or aria-\* attributes).

### Example of ElementInternals (normal web-component)

```ts
class CustomLinkComponent extends HTMLElement {
  constructor() {
    this._internals = this.attachInternals();
    this._internals.role = 'link';
  }

  static tagName = 'custom-link-component';
}
```

## Why do we need ElementInternals

We as developers from OIP require from each website element that it is
accessible. Without ElementInternals we are limited to use json to render
tables, lists, accordions, dialogs and many more semantic HTML elements.

> The web component only renders the outline, the json is used to render the
> preact elements.

## What do we require from the register API.

We require an options to define internals. There are two options for this:

1. We can add the internals to the register options.
2. We can implement it like formAssociated.

## Are there limitations if we use ElementInternals

Yes, we can't use the `is=""` attribute on web-components.

## Conclusion

We (OIP team) have multiple options on how we continue working on
web-components:

1. We can build the entire register function ourselves (inside the OIP repo)
2. Fork the repo and maintain our own clone (own repo)
3. Fork the repo and send in a PR containing the required changes
4. Only create an issue for it.

| Solution | Pro's.                           | Con's                       |
| -------- | -------------------------------- | --------------------------- |
| 1        | Complete flexibility             | No updates                  |
| 2        | Complete flexibility             | No updates                  |
| 3        | Don't have to maintain ourselves | Dependent on approval       |
| 4        | Don't have to maintain ourselves | Dependent on implementation |

### My own opinion

Considering the size of `PCE` we can implement it on our own. I recommend
**option 1: building our own register function**. This gives us:

- Full control over the implementation
- No dependency on external maintainers for critical accessibility features
- Ability to extend with OIP-specific features (plugins, i18n wrapping, etc.)

The trade-off of not receiving upstream updates is minimal since PCE is stable
and we're already extending its functionality significantly with the
`WebComponentLoader` class.

---

## Implementation Approach

We have chosen to implement our own web component registration system that
supports ElementInternals. This is done through the `WebComponentLoader` class.

### Type Definitions

```ts
// From types.ts
export interface InternalsConfig {
  role?: string;
  ariaLabel?: string;
  ariaBusy?: string;
  ariaDisabled?: string;
  ariaExpanded?: string;
  ariaHidden?: string;
  ariaSelected?: string;
  ariaChecked?: string;
  ariaPressed?: string;
}

export type WebComponentRegisterExtraOptions = {
  i18n?: boolean;
  formAssociated?: boolean;
  internals?: InternalsConfig;
};
```

### Proposed API Usage

```ts
// In a component's constants.ts
export const TABLE_DEFINITION: WebComponentDefinition<
  'oip-table',
  ITableProps
> = {
  tagName: 'oip-table',
  propNames: ['data'],
  options: {
    shadow: false,
    internals: {
      role: 'table',
      ariaLabel: 'Data table',
    },
  },
  importer: () => import('./Table'),
};
```

### How ElementInternals Works

When a custom element uses `attachInternals()`, it must:

1. **Not extend a built-in element** - Cannot use `is=""` attribute
2. **Call `attachInternals()` in the constructor** - Only once per element
3. **Optionally set `formAssociated = true`** - For form participation

```ts
class OipTable extends HTMLElement {
  static formAssociated = true; // Optional: for form elements

  constructor() {
    super();
    const internals = this.attachInternals();
    internals.role = 'table';
    internals.ariaLabel = 'Data table';
  }
}
```

### Integration with Preact

The challenge with PCE is that it creates the custom element class internally.
To support ElementInternals, we need to either:

1. **Patch the generated class** - Add `attachInternals()` call after PCE
   creates the class
2. **Create our own class factory** - Build the HTMLElement subclass ourselves
   and use Preact only for rendering

We chose option 2 for maximum control and flexibility.

---

## Current Implementation Status

| Feature              | Status         | Notes                            |
| -------------------- | -------------- | -------------------------------- |
| InternalsConfig type | ✅ Complete    | Defined in `types.ts`            |
| Register options     | ✅ Complete    | Added to registration options    |
| Loader integration   | 🚧 In Progress | Config extracted but not applied |
| Component usage      | ⏳ Pending     | Waiting for loader completion    |
| Documentation        | 🚧 In Progress | This document                    |

---

## Testing ElementInternals

A test component exists at `components/TestInternals/` demonstrating vanilla web
component internals:

```ts
class CustomCheckbox extends HTMLElement {
  static formAssociated = true;
  internals_;

  constructor() {
    super();
    this.internals_ = this.attachInternals();
    this.internals_.role = 'checkbox';
  }
}
```

This verifies browser support and expected behavior before integrating with
Preact components.

---

## Browser Support

ElementInternals is supported in all modern browsers:

| Browser | Version |
| ------- | ------- |
| Chrome  | 77+     |
| Firefox | 93+     |
| Safari  | 16.4+   |
| Edge    | 79+     |

For older browsers, a polyfill may be required:
[element-internals-polyfill](https://www.npmjs.com/package/element-internals-polyfill)

---

## References

- [MDN: ElementInternals](https://developer.mozilla.org/en-US/docs/Web/API/ElementInternals)
- [MDN: attachInternals()](https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/attachInternals)
- [Web.dev: More capable form controls](https://web.dev/articles/more-capable-form-controls)
- [WHATWG: Custom Element Internals](https://html.spec.whatwg.org/multipage/custom-elements.html#elementinternals)
- [preact-custom-element source](https://github.com/preactjs/preact-custom-element)
