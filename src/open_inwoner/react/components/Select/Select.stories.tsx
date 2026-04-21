import { withLoader } from '@react/lib/decorators';
import type { Meta, StoryObj } from '@storybook/preact-vite';
import { SELECT_DEFINITION, SELECT_OPTION_DEFINITION } from './constants';

/**
 * oip-select — standalone select/dropdown component.
 *
 * Composes with oip-select-option via SelectContext. No root context required —
 * Select manages its own signal state when used standalone.
 */

const meta: Meta = {
  title: 'Debug/Select2',
  decorators: [withLoader(SELECT_DEFINITION.tagName)],
  parameters: { layout: 'padded' },
};

export default meta;
type Story = StoryObj;

/** Default dropdown — no pre-selected items. */
export const Dropdown: Story = {
  render: () => (
    <oip-select name="status" label="Status">
      <oip-select-option value="open" label="Open" />
      <oip-select-option value="in-behandeling" label="In behandeling" />
      <oip-select-option value="afgerond" label="Afgerond" />
      <oip-select-option value="geannuleerd" label="Geannuleerd" />
    </oip-select>
  ),
};

/** Button label shows count when items are pre-selected. */
export const DropdownWithSelection: Story = {
  render: () => (
    <oip-select name="status" label="Status">
      <oip-select-option value="open" label="Open" initial-selected="true" />
      <oip-select-option
        value="in-behandeling"
        label="In behandeling"
        initial-selected="true"
      />
      <oip-select-option value="afgerond" label="Afgerond" />
      <oip-select-option value="geannuleerd" label="Geannuleerd" />
    </oip-select>
  ),
};

/** Fieldset layout — choices always visible, no toggle button. */
export const AlwaysOpen: Story = {
  render: () => (
    <oip-select name="status" label="Status" always-open="true">
      <oip-select-option value="open" label="Open" />
      <oip-select-option value="in-behandeling" label="In behandeling" />
      <oip-select-option value="afgerond" label="Afgerond" />
      <oip-select-option value="geannuleerd" label="Geannuleerd" />
    </oip-select>
  ),
};

/** Radio group — only one value can be active at a time. */
export const RadioGroup: Story = {
  render: () => (
    <oip-select name="datum" label="Datum (kies één)" multiple="false">
      <oip-select-option value="week" label="Afgelopen week" />
      <oip-select-option value="maand" label="Afgelopen maand" />
      <oip-select-option value="jaar" label="Afgelopen jaar" />
    </oip-select>
  ),
};
