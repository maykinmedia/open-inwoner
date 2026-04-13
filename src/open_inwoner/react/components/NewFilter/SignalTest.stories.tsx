/**
 * NewFilter stories — rebuilds the Filters component using the signal/self-registration approach.
 *
 * Architecture:
 *   oip-sig-root-test    — creates Signal<selected>, handles isDirty + applyFilters
 *     oip-sig-bar-test   — desktop bar (groups + apply button) / mobile button + modal
 *       oip-sig-list-test  — a filter group (dropdown on desktop, fieldset on mobile)
 *         oip-sig-option-test — single option; registers its group, value and label on mount
 *     oip-sig-summary-test — renders chips for active filters + clear-all button
 *
 * No JSON config is needed — the HTML is the config.
 * Initial state (e.g. from URL params) is expressed via initial-selected on each option.
 */
import { withLoader } from '@react/lib/decorators';
import type { Meta, StoryObj } from '@storybook/preact-vite';
import { NEW_FILTER_ROOT_DEFINITION } from './constants';

const meta: Meta = {
  title: 'Debug/NewFilter',
  decorators: [withLoader(NEW_FILTER_ROOT_DEFINITION.tagName)],
  parameters: { layout: 'padded' },
};

export default meta;

/** Default — no filters pre-selected. */
export const Default: StoryObj = {
  render: () => (
    <oip-sig-root-test>
      <oip-sig-bar-test>
        <oip-sig-list-test name="status" label="Status">
          <oip-sig-option-test group="status" value="open" label="Open" />
          <oip-sig-option-test
            group="status"
            value="in-behandeling"
            label="In behandeling"
          />
          <oip-sig-option-test
            group="status"
            value="afgerond"
            label="Afgerond"
          />
          <oip-sig-option-test
            group="status"
            value="geannuleerd"
            label="Geannuleerd"
          />
        </oip-sig-list-test>
        <oip-sig-list-test name="categorie" label="Categorie">
          <oip-sig-option-test group="categorie" value="vraag" label="Vraag" />
          <oip-sig-option-test
            group="categorie"
            value="melding"
            label="Melding"
          />
          <oip-sig-option-test
            group="categorie"
            value="klacht"
            label="Klacht"
          />
        </oip-sig-list-test>
        <oip-sig-list-test name="datum" label="Datum">
          <oip-sig-option-test
            group="datum"
            value="week"
            label="Afgelopen week"
          />
          <oip-sig-option-test
            group="datum"
            value="maand"
            label="Afgelopen maand"
          />
          <oip-sig-option-test
            group="datum"
            value="jaar"
            label="Afgelopen jaar"
          />
        </oip-sig-list-test>
      </oip-sig-bar-test>
      <oip-sig-summary-test />
    </oip-sig-root-test>
  ),
};

/** Pre-selected filters — simulates page load from URL params. */
export const WithActiveFilters: StoryObj = {
  render: () => (
    <oip-sig-root-test>
      <oip-sig-bar-test>
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
          <oip-sig-option-test
            group="status"
            value="afgerond"
            label="Afgerond"
          />
          <oip-sig-option-test
            group="status"
            value="geannuleerd"
            label="Geannuleerd"
          />
        </oip-sig-list-test>
        <oip-sig-list-test name="categorie" label="Categorie">
          <oip-sig-option-test group="categorie" value="vraag" label="Vraag" />
          <oip-sig-option-test
            group="categorie"
            value="melding"
            label="Melding"
            initial-selected="true"
          />
          <oip-sig-option-test
            group="categorie"
            value="klacht"
            label="Klacht"
          />
        </oip-sig-list-test>
        <oip-sig-list-test name="datum" label="Datum">
          <oip-sig-option-test
            group="datum"
            value="week"
            label="Afgelopen week"
          />
          <oip-sig-option-test
            group="datum"
            value="maand"
            label="Afgelopen maand"
          />
          <oip-sig-option-test
            group="datum"
            value="jaar"
            label="Afgelopen jaar"
          />
        </oip-sig-list-test>
      </oip-sig-bar-test>
      <oip-sig-summary-test />
    </oip-sig-root-test>
  ),
};

/** Radio (single-select) group alongside checkbox groups. */
export const WithRadioGroup: StoryObj = {
  render: () => (
    <oip-sig-root-test>
      <oip-sig-bar-test>
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
          />
          <oip-sig-option-test
            group="status"
            value="afgerond"
            label="Afgerond"
          />
        </oip-sig-list-test>
        <oip-sig-list-test name="datum" label="Datum (kies één)">
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
      </oip-sig-bar-test>
      <oip-sig-summary-test />
    </oip-sig-root-test>
  ),
};
