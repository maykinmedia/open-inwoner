import { withLoader } from '@react/lib/decorators';
import type { Meta, StoryObj } from '@storybook/preact-vite';
import { SELECT_DEFINITION, SELECT_OPTION_DEFINITION } from './constants';

const meta: Meta = {
  title: 'Debug/Select',
  decorators: [
    withLoader(SELECT_DEFINITION.tagName, SELECT_OPTION_DEFINITION.tagName),
  ],
  parameters: { layout: 'padded' },
};

export default meta;
type Story = StoryObj;

/** Dropdown — no pre-selected items. */
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

/** Fieldset with pre-selected items. */
export const AlwaysOpenWithSelection: Story = {
  render: () => (
    <oip-select name="status" label="Status" always-open="true">
      <oip-select-option value="open" label="Open" initial-selected="true" />
      <oip-select-option value="in-behandeling" label="In behandeling" />
      <oip-select-option
        value="afgerond"
        label="Afgerond"
        initial-selected="true"
      />
      <oip-select-option value="geannuleerd" label="Geannuleerd" />
    </oip-select>
  ),
};

/** Radio group — only one value active at a time. */
export const RadioGroup: Story = {
  render: () => (
    <oip-select name="datum" label="Datum (kies één)" multiple="false">
      <oip-select-option value="week" label="Afgelopen week" />
      <oip-select-option value="maand" label="Afgelopen maand" />
      <oip-select-option value="jaar" label="Afgelopen jaar" />
    </oip-select>
  ),
};

/** Radio group with a pre-selected value. */
export const RadioGroupWithSelection: Story = {
  render: () => (
    <oip-select name="datum" label="Datum (kies één)" multiple="false">
      <oip-select-option
        value="week"
        label="Afgelopen week"
        initial-selected="true"
      />
      <oip-select-option value="maand" label="Afgelopen maand" />
      <oip-select-option value="jaar" label="Afgelopen jaar" />
    </oip-select>
  ),
};

/** Multiple selects side by side — desktop bar layout. */
export const MultipleSelects: Story = {
  render: () => (
    <div style="display: flex; gap: 8px; align-items: flex-start">
      <oip-select name="status" label="Status">
        <oip-select-option value="open" label="Open" initial-selected="true" />
        <oip-select-option value="afgerond" label="Afgerond" />
      </oip-select>
      <oip-select name="categorie" label="Categorie">
        <oip-select-option value="vraag" label="Vraag" />
        <oip-select-option value="melding" label="Melding" />
      </oip-select>
      <oip-select name="datum" label="Datum (kies één)" multiple="false">
        <oip-select-option value="week" label="Afgelopen week" />
        <oip-select-option value="maand" label="Afgelopen maand" />
      </oip-select>
    </div>
  ),
};

/** Inside a form — oip-select is form-associated, values appear in FormData on submit. */
export const InsideForm: Story = {
  render: () => (
    <form
      method="GET"
      action=""
      onSubmit={(e) => {
        e.preventDefault();
        const fd = new FormData(e.currentTarget as HTMLFormElement);
        console.log('FormData:', Object.fromEntries(fd));
      }}
    >
      <oip-select name="status" label="Status">
        <oip-select-option value="open" label="Open" initial-selected="true" />
        <oip-select-option value="in-behandeling" label="In behandeling" />
        <oip-select-option value="afgerond" label="Afgerond" />
      </oip-select>
      <button type="submit" style="margin-top: 8px; display: block">
        Submit (check console)
      </button>
    </form>
  ),
};
