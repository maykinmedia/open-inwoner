import {
  withFormContext,
  withFilterContext,
  withLoader,
} from '@react/lib/decorators/storybook';
import type { Meta, StoryObj } from '@storybook/preact-vite';
import { FIELDSET_OPTION_DEFINITION } from './constants';
import { FIELDSET_DEFINITION } from '../Fieldset/constants';

/**
 * `oip-fieldset-option` is a single checkbox or radio option inside
 * `oip-fieldset`. It must always be a direct child of `oip-fieldset` —
 * it renders nothing without a `FieldsetContext`.
 *
 * ## HTML API
 *
 * ```html
 * <oip-fieldset name="status" label="Status">
 *   <oip-fieldset-option value="open"          label="Open" />
 *   <oip-fieldset-option value="in-behandeling" label="In behandeling" />
 * </oip-fieldset>
 * ```
 *
 * ## Props
 *
 * | Prop    | Type     | Description |
 * |---------|----------|-------------|
 * | `value` | `string` | The raw value stored in FormContext when selected. Must match the URL query param value. |
 * | `label` | `string` | The display string shown next to the input and registered with FilterContext for chip text. |
 *
 * ## Default selection
 *
 * Do **not** set default selection here. Use the `value` attribute on the
 * parent `oip-fieldset` instead:
 *
 * ```html
 * <!-- ✓ correct -->
 * <oip-fieldset name="status" value="open">
 *   <oip-fieldset-option value="open" label="Open" />
 * </oip-fieldset>
 * ```
 *
 * ## oip-select-option vs oip-fieldset-option
 *
 * | | `oip-select-option` | `oip-fieldset-option` |
 * |---|---|---|
 * | Parent | `oip-select` | `oip-fieldset` |
 * | Interaction | Custom div + keyboard nav | Native `<label><input>` |
 * | Focus management | Managed by Select (arrow keys, typeahead) | Native browser behaviour |
 * | Accessibility | `role="option"` via ElementInternals | Native `<input type="checkbox/radio">` |
 */
const meta: Meta = {
  title: 'Components/FieldsetOption',
  decorators: [
    withFilterContext,
    withFormContext,
    withLoader(FIELDSET_DEFINITION.tagName, FIELDSET_OPTION_DEFINITION.tagName),
  ],
  parameters: { layout: 'padded' },
};

export default meta;
type Story = StoryObj;

/**
 * Default checkbox options. No item is pre-selected.
 */
export const Default: Story = {
  render: () => (
    <oip-fieldset name="status" label="Status">
      <oip-fieldset-option value="open" label="Open" />
      <oip-fieldset-option value="in-behandeling" label="In behandeling" />
      <oip-fieldset-option value="afgerond" label="Afgerond" />
      <oip-fieldset-option value="geannuleerd" label="Geannuleerd" />
    </oip-fieldset>
  ),
};

/**
 * Pre-selected values set via `value` on the parent `oip-fieldset`.
 */
export const WithPreselectedValues: Story = {
  render: () => (
    <oip-fieldset name="status" label="Status" value="open,afgerond">
      <oip-fieldset-option value="open" label="Open" />
      <oip-fieldset-option value="in-behandeling" label="In behandeling" />
      <oip-fieldset-option value="afgerond" label="Afgerond" />
      <oip-fieldset-option value="geannuleerd" label="Geannuleerd" />
    </oip-fieldset>
  ),
};

/**
 * Radio mode (`multiple="false"` on the parent).
 * Options render as `<input type="radio">` — selecting one clears the others.
 */
export const RadioMode: Story = {
  render: () => (
    <oip-fieldset name="periode" label="Periode" multiple="false">
      <oip-fieldset-option value="2025" label="Jaar 2025" />
      <oip-fieldset-option value="2024" label="Jaar 2024" />
      <oip-fieldset-option value="2023" label="Jaar 2023" />
    </oip-fieldset>
  ),
};
