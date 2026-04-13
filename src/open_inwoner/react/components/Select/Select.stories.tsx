import { withLoader } from '@react/lib/decorators';
import type { Meta, StoryObj } from '@storybook/preact-vite';
import { SELECT_DEFINITION, SELECT_OPTION_DEFINITION } from './constants';

/**
 * oip-sig-list-test — standalone select/dropdown component.
 *
 * Composes with oip-sig-option-test via SelectContext. No root context
 * (oip-sig-root-test) required — Select manages its own signal state when
 * used standalone.
 */

const meta: Meta = {
  title: 'Debug/Select',
  decorators: [
    withLoader(SELECT_DEFINITION.tagName, SELECT_OPTION_DEFINITION.tagName),
  ],
  parameters: { layout: 'padded' },
};

export default meta;
type Story = StoryObj;

/** Default dropdown — no pre-selected items. */
export const Dropdown: Story = {
  render: () => (
    <oip-sig-list-test name="status" label="Status">
      <oip-sig-option-test group="status" value="open" label="Open" />
      <oip-sig-option-test
        group="status"
        value="in-behandeling"
        label="In behandeling"
      />
      <oip-sig-option-test group="status" value="afgerond" label="Afgerond" />
      <oip-sig-option-test
        group="status"
        value="geannuleerd"
        label="Geannuleerd"
      />
    </oip-sig-list-test>
  ),
};

/** Button label shows count when items are pre-selected. */
export const DropdownWithSelection: Story = {
  render: () => (
    <oip-sig-list-test name="status" label="Status">
      <oip-sig-option-test
        group="status"
        value="open"
        label="Open"
        initial-selected="true"
      />
      <oip-sig-option-test
        group="status"
        value="in-behandeling"
        label="In behandeling"
        initial-selected="true"
      />
      <oip-sig-option-test group="status" value="afgerond" label="Afgerond" />
      <oip-sig-option-test
        group="status"
        value="geannuleerd"
        label="Geannuleerd"
      />
    </oip-sig-list-test>
  ),
};

/** Fieldset layout — choices always visible, no toggle button. */
export const AlwaysOpen: Story = {
  render: () => (
    <oip-sig-list-test name="status" label="Status" always-open="true">
      <oip-sig-option-test group="status" value="open" label="Open" />
      <oip-sig-option-test
        group="status"
        value="in-behandeling"
        label="In behandeling"
      />
      <oip-sig-option-test group="status" value="afgerond" label="Afgerond" />
      <oip-sig-option-test
        group="status"
        value="geannuleerd"
        label="Geannuleerd"
      />
    </oip-sig-list-test>
  ),
};

/** Radio group — only one value can be active at a time. */
export const RadioGroup: Story = {
  render: () => (
    <oip-sig-list-test name="datum" label="Datum (kies één)" multiple="false">
      <oip-sig-option-test
        group="datum"
        value="week"
        label="Afgelopen week"
        checkbox="false"
      />
      <oip-sig-option-test
        group="datum"
        value="maand"
        label="Afgelopen maand"
        checkbox="false"
      />
      <oip-sig-option-test
        group="datum"
        value="jaar"
        label="Afgelopen jaar"
        checkbox="false"
      />
    </oip-sig-list-test>
  ),
};
