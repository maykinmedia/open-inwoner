import {
  withFormContext,
  withFilterContext,
  withLoader,
} from '@react/lib/decorators/storybook';
import type { Meta, StoryObj } from '@storybook/preact-vite';
import { FIELDSET_DEFINITION } from './constants';
import { FIELDSET_OPTION_DEFINITION } from '../FieldsetOption/constants';

/**
 * `oip-fieldset` is an inline filter field — the same data layer as
 * `oip-select` but rendered as a visible list of checkboxes or radios rather
 * than a dropdown. Designed for use inside `oip-filter-modal` where all
 * options should be visible at once without a toggle.
 *
 * ## HTML API
 *
 * ```html
 * <oip-fieldset
 *   name="status"
 *   label="Status"
 *   value="open,afgerond"
 *   multiple="true"
 * >
 *   <oip-fieldset-option value="open"          label="Open" />
 *   <oip-fieldset-option value="in-behandeling" label="In behandeling" />
 *   <oip-fieldset-option value="afgerond"       label="Afgerond" />
 * </oip-fieldset>
 * ```
 *
 * ## Props
 *
 * | Prop       | Type      | Default | Description |
 * |------------|-----------|---------|-------------|
 * | `name`     | `string`  | —       | Field name. Must match the URL query param name and the corresponding `oip-select` name if both are used. |
 * | `label`    | `string`  | —       | Rendered as a `<legend>` above the option list. |
 * | `value`    | `string`  | `""`    | Comma-separated pre-selected values. Read from the URL by Django and passed as an attribute. |
 * | `multiple` | `boolean` | `true`  | `true` → checkboxes. `false` → radio buttons (single-select). |
 *
 * ## Context requirements
 *
 * `oip-fieldset` requires **both** `oip-form` (FormContext) and `oip-filters`
 * (FilterContext). It registers option labels with FilterContext so
 * `oip-filter-chips` can display readable chip text.
 *
 * ```html
 * <oip-form>
 *   <oip-filters>
 *     <oip-fieldset name="status" label="Status">
 *       <oip-fieldset-option value="open" label="Open" />
 *     </oip-fieldset>
 *   </oip-filters>
 * </oip-form>
 * ```
 *
 * Without `oip-filters` the component renders nothing (`withContextGuard`
 * returns `null`). This is stricter than `oip-select`, which only requires
 * `oip-form`.
 *
 * ## oip-select vs oip-fieldset
 *
 * | | `oip-select` | `oip-fieldset` |
 * |---|---|---|
 * | Layout | Dropdown (toggle button) | Always-visible list |
 * | Keyboard nav | Arrow keys, typeahead | Native browser tab/space |
 * | Use case | Desktop filter bar | Mobile filter modal |
 * | Requires | `oip-form` | `oip-form` + `oip-filters` |
 *
 * Both write to the same `FormContext` field, so `name` must be identical
 * when a field appears in both the desktop bar and the mobile modal.
 */
const meta: Meta = {
  title: 'Components/Fieldset',
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
 * Default fieldset — checkboxes, no pre-selected values.
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
 * Pre-selected values via the `value` attribute (comma-separated).
 * "Open" and "Afgerond" render checked.
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
 * Single-select (radio) mode via `multiple="false"`.
 * Selecting one option deselects any previously selected option.
 */
export const SingleSelect: Story = {
  render: () => (
    <oip-fieldset name="periode" label="Periode" multiple="false">
      <oip-fieldset-option value="2025" label="Jaar 2025" />
      <oip-fieldset-option value="2024" label="Jaar 2024" />
      <oip-fieldset-option value="2023" label="Jaar 2023" />
    </oip-fieldset>
  ),
};

/**
 * Multiple fieldsets — mirrors a full mobile modal filter panel.
 */
export const MultipleFieldsets: Story = {
  render: () => (
    <div style="display: flex; flex-direction: column; gap: 16px">
      <oip-fieldset name="status" label="Status">
        <oip-fieldset-option value="open" label="Open" />
        <oip-fieldset-option value="afgerond" label="Afgerond" />
      </oip-fieldset>
      <oip-fieldset name="periode" label="Periode" multiple="false">
        <oip-fieldset-option value="2025" label="Jaar 2025" />
        <oip-fieldset-option value="2024" label="Jaar 2024" />
      </oip-fieldset>
    </div>
  ),
};
