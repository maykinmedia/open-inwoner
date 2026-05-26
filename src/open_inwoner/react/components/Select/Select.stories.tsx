import {
  withFormContext,
  withFilterContext,
  withLoader,
} from '@react/lib/decorators/storybook';
import type { Meta, StoryObj } from '@storybook/preact-vite';
import { SELECT_DEFINITION } from './constants';

/**
 * `oip-select` is a dropdown filter field backed by `FormContext`.
 *
 * ## HTML API
 *
 * ```html
 * <oip-select
 *   name="status"
 *   label="Status"
 *   value="open,afgerond"
 *   multiple="true"
 * >
 *   <oip-select-option value="open"        label="Open" />
 *   <oip-select-option value="in-behandeling" label="In behandeling" />
 *   <oip-select-option value="afgerond"    label="Afgerond" />
 * </oip-select>
 * ```
 *
 * ## Props
 *
 * | Prop       | Type      | Default  | Description |
 * |------------|-----------|----------|-------------|
 * | `name`     | `string`  | -        | Field name. Must match the URL query param name. |
 * | `label`    | `string`  | -        | Button label. Shows `Label (n)` when n items are selected. |
 * | `value`    | `string`  | `""`     | Comma-separated list of pre-selected values, e.g. `"open,afgerond"`. Read from the URL by Django and passed as an attribute. |
 * | `multiple` | `boolean` | `true`   | `true` → checkbox semantics (multi-select). `false` → radio semantics (single-select). |
 *
 * ## Context requirements
 *
 * `oip-select` **requires** `oip-form` (FormContext) to manage field values.
 * `oip-filters` (FilterContext) is **optional** - when present, labels are
 * registered so `oip-filter-chips` can display readable chip text.
 *
 * ```html
 * <oip-form>
 *   <oip-filters>
 *     <oip-select name="status" label="Status">
 *       <oip-select-option value="open" label="Open" />
 *     </oip-select>
 *   </oip-filters>
 * </oip-form>
 * ```
 *
 * Without `oip-form` the component renders nothing (`withContextGuard` returns `null`).
 *
 * ## Default values
 *
 * Default selection is set via the `value` attribute on `oip-select`, not on
 * individual `oip-select-option` elements. In a Django template:
 *
 * ```html
 * <oip-select name="status" value="{{ request.GET.status }}">
 * ```
 *
 * For multi-select fields with multiple URL params join them server-side:
 *
 * ```html
 * <oip-select name="type" value="{{ request.GET.getlist('type')|join:',' }}">
 * ```
 */
const meta: Meta = {
  title: 'Components/Select',
  decorators: [
    withFilterContext,
    withFormContext,
    withLoader(SELECT_DEFINITION.tagName),
  ],
  parameters: { layout: 'padded' },
};

export default meta;
type Story = StoryObj;

/**
 * Default dropdown with no pre-selected values.
 * Click the button to open and toggle options.
 */
export const Default: Story = {
  render: () => (
    <oip-select name="status" label="Status">
      <oip-select-option value="open" label="Open" />
      <oip-select-option value="in-behandeling" label="In behandeling" />
      <oip-select-option value="afgerond" label="Afgerond" />
      <oip-select-option value="geannuleerd" label="Geannuleerd" />
    </oip-select>
  ),
};

/**
 * Pre-selected values via the `value` attribute (comma-separated).
 * The button label shows the count: "Status (2)".
 */
export const WithPreselectedValues: Story = {
  render: () => (
    <oip-select name="status" label="Status" value="open,in-behandeling">
      <oip-select-option value="open" label="Open" />
      <oip-select-option value="in-behandeling" label="In behandeling" />
      <oip-select-option value="afgerond" label="Afgerond" />
      <oip-select-option value="geannuleerd" label="Geannuleerd" />
    </oip-select>
  ),
};

/**
 * Single-select (radio) mode via `multiple="false"`.
 * Selecting a new value replaces the current selection.
 */
export const SingleSelect: Story = {
  render: () => (
    <oip-select name="periode" label="Periode" multiple="false">
      <oip-select-option value="2025" label="Jaar 2025" />
      <oip-select-option value="2024" label="Jaar 2024" />
      <oip-select-option value="2023" label="Jaar 2023" />
    </oip-select>
  ),
};

/**
 * Single-select with a pre-selected value.
 * The button label shows "Periode (1)".
 */
export const SingleSelectWithValue: Story = {
  render: () => (
    <oip-select name="periode" label="Periode" multiple="false" value="2025">
      <oip-select-option value="2025" label="Jaar 2025" />
      <oip-select-option value="2024" label="Jaar 2024" />
      <oip-select-option value="2023" label="Jaar 2023" />
    </oip-select>
  ),
};

/**
 * Multiple selects side by side - desktop filter bar layout.
 * Each select manages its own open/close state independently.
 */
export const FilterBar: Story = {
  render: () => (
    <div style="display: flex; gap: 8px; align-items: flex-start">
      <oip-select name="status" label="Status" value="open">
        <oip-select-option value="open" label="Open" />
        <oip-select-option value="afgerond" label="Afgerond" />
      </oip-select>
      <oip-select name="categorie" label="Categorie">
        <oip-select-option value="vraag" label="Vraag" />
        <oip-select-option value="melding" label="Melding" />
      </oip-select>
      <oip-select name="periode" label="Periode" multiple="false">
        <oip-select-option value="2025" label="Jaar 2025" />
        <oip-select-option value="2024" label="Jaar 2024" />
      </oip-select>
    </div>
  ),
};

/**
 * Many options - verifies scroll behaviour inside the dropdown.
 * The choices panel is capped at 300 px and scrolls internally.
 */
export const ManyOptions: Story = {
  render: () => (
    <oip-select name="categorie" label="Categorie">
      {Array.from({ length: 20 }, (_, i) => (
        <oip-select-option
          key={i}
          value={`option-${i}`}
          label={`Optie ${i + 1}`}
        />
      ))}
    </oip-select>
  ),
};
