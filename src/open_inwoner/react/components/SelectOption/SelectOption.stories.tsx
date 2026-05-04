import {
  withFormContext,
  withFilterContext,
  withLoader,
} from '@react/lib/decorators/storybook';
import type { Meta, StoryObj } from '@storybook/preact-vite';
import { SELECT_OPTION_DEFINITION } from './constants';
import { SELECT_DEFINITION } from '../Select/constants';

/**
 * `oip-select-option` is a single option row inside `oip-select`.
 *
 * It must always be a direct child of `oip-select` — it renders nothing
 * on its own (`withContextGuard` returns `null` without a `SelectContext`).
 *
 * ## HTML API
 *
 * ```html
 * <oip-select name="status" label="Status">
 *   <oip-select-option value="open"          label="Open" />
 *   <oip-select-option value="in-behandeling" label="In behandeling" />
 *   <oip-select-option value="afgerond"       label="Afgerond" />
 * </oip-select>
 * ```
 *
 * ## Props
 *
 * | Prop    | Type     | Description |
 * |---------|----------|-------------|
 * | `value` | `string` | The raw value stored in FormContext when this option is selected. Must match the URL query param value. |
 * | `label` | `string` | The display string shown in the option row and registered with FilterContext for chip text. |
 *
 * ## Default selection
 *
 * Do **not** set default selection here. Use the `value` attribute on the
 * parent `oip-select` instead:
 *
 * ```html
 * <!-- ✓ correct -->
 * <oip-select name="status" value="open">
 *   <oip-select-option value="open" label="Open" />
 * </oip-select>
 *
 * <!-- ✗ wrong — initial-selected does not exist -->
 * <oip-select-option value="open" label="Open" initial-selected="true" />
 * ```
 *
 * ## Keyboard navigation
 *
 * When the dropdown is open, each option handles:
 *
 * | Key           | Behaviour |
 * |---------------|-----------|
 * | `ArrowDown`   | Move focus to next option |
 * | `ArrowUp`     | Move focus to previous option |
 * | `Enter` / ` ` | Toggle selection |
 * | `Escape`      | Close dropdown, return focus to toggle button |
 * | `Tab`         | Close dropdown |
 * | Printable char | Typeahead: jump to first option whose label starts with that character |
 *
 * ## Accessibility
 *
 * - The host element has `role="option"` via `ElementInternals`.
 * - `ariaSelected` on the host is kept in sync with the selection state.
 * - The `<input>` inside the shadow root is `aria-hidden` — it exists only
 *   for CSS-driven checkbox/radio icon state.
 */
const meta: Meta = {
  title: 'Components/SelectOption',
  decorators: [
    withFilterContext,
    withFormContext,
    withLoader(SELECT_DEFINITION.tagName, SELECT_OPTION_DEFINITION.tagName),
  ],
  parameters: { layout: 'padded' },
};

export default meta;
type Story = StoryObj;

/**
 * Default multi-select options. No item is pre-selected.
 * Click an option to toggle it; the checkbox icon updates immediately.
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
 * Options with pre-selected values set via `value` on the parent `oip-select`.
 * "Open" and "Afgerond" render with their checkbox icons checked.
 */
export const WithPreselectedValues: Story = {
  render: () => (
    <oip-select name="status" label="Status" value="open,afgerond">
      <oip-select-option value="open" label="Open" />
      <oip-select-option value="in-behandeling" label="In behandeling" />
      <oip-select-option value="afgerond" label="Afgerond" />
      <oip-select-option value="geannuleerd" label="Geannuleerd" />
    </oip-select>
  ),
};

/**
 * Radio mode (`multiple="false"` on the parent).
 * Options render with radio icons; selecting one deselects the others.
 */
export const RadioMode: Story = {
  render: () => (
    <oip-select name="periode" label="Periode" multiple="false">
      <oip-select-option value="2025" label="Jaar 2025" />
      <oip-select-option value="2024" label="Jaar 2024" />
      <oip-select-option value="2023" label="Jaar 2023" />
    </oip-select>
  ),
};
