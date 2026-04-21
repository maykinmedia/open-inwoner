/**
 * NewFilter stories — rebuilds the Filters component using the signal/self-registration approach.
 *
 * Architecture:
 *   <form method="GET">          — native form for GET submission (optional, enables requestSubmit)
 *     oip-sig-root-test          — creates Signal<selected>, handles isDirty + applyFilters
 *       oip-sig-bar-test         — desktop bar / mobile button + modal
 *         oip-filter-select      — filter group (dropdown or fieldset); formAssociated
 *           oip-select-option    — registers value/label on mount
 *       oip-sig-summary-test     — chips for active filters + clear-all
 *
 * applyFilters() calls form.requestSubmit() when a <form> ancestor is present,
 * falling back to window.location.assign() otherwise.
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

/** With native form — applyFilters calls form.requestSubmit(). */
export const WithForm: StoryObj = {
  render: () => (
    <form method="GET" action="">
      <oip-sig-root-test>
        <oip-sig-bar-test>
          <oip-filter-select name="status" label="Status">
            <oip-select-option value="open" label="Open" />
            <oip-select-option value="in-behandeling" label="In behandeling" />
            <oip-select-option value="afgerond" label="Afgerond" />
            <oip-select-option value="geannuleerd" label="Geannuleerd" />
          </oip-filter-select>
          <oip-filter-select name="categorie" label="Categorie">
            <oip-select-option value="vraag" label="Vraag" />
            <oip-select-option value="melding" label="Melding" />
            <oip-select-option value="klacht" label="Klacht" />
          </oip-filter-select>
          <oip-filter-select name="datum" label="Datum">
            <oip-select-option value="week" label="Afgelopen week" />
            <oip-select-option value="maand" label="Afgelopen maand" />
            <oip-select-option value="jaar" label="Afgelopen jaar" />
          </oip-filter-select>
        </oip-sig-bar-test>
        <oip-sig-summary-test />
      </oip-sig-root-test>
    </form>
  ),
};

/** Without form — applyFilters falls back to window.location.assign(). */
export const Default: StoryObj = {
  render: () => (
    <oip-sig-root-test>
      <oip-sig-bar-test>
        <oip-filter-select name="status" label="Status">
          <oip-select-option value="open" label="Open" />
          <oip-select-option value="in-behandeling" label="In behandeling" />
          <oip-select-option value="afgerond" label="Afgerond" />
          <oip-select-option value="geannuleerd" label="Geannuleerd" />
        </oip-filter-select>
        <oip-filter-select name="categorie" label="Categorie">
          <oip-select-option value="vraag" label="Vraag" />
          <oip-select-option value="melding" label="Melding" />
          <oip-select-option value="klacht" label="Klacht" />
        </oip-filter-select>
        <oip-filter-select name="datum" label="Datum">
          <oip-select-option value="week" label="Afgelopen week" />
          <oip-select-option value="maand" label="Afgelopen maand" />
          <oip-select-option value="jaar" label="Afgelopen jaar" />
        </oip-filter-select>
      </oip-sig-bar-test>
      <oip-sig-summary-test />
    </oip-sig-root-test>
  ),
};

/** Pre-selected filters — simulates page load from URL params. */
export const WithActiveFilters: StoryObj = {
  render: () => (
    <form method="GET" action="">
      <oip-sig-root-test>
        <oip-sig-bar-test>
          <oip-filter-select name="status" label="Status">
            <oip-select-option
              value="open"
              label="Open"
              initial-selected="true"
            />
            <oip-select-option
              value="in-behandeling"
              label="In behandeling"
              initial-selected="true"
            />
            <oip-select-option value="afgerond" label="Afgerond" />
            <oip-select-option value="geannuleerd" label="Geannuleerd" />
          </oip-filter-select>
          <oip-filter-select name="categorie" label="Categorie">
            <oip-select-option value="vraag" label="Vraag" />
            <oip-select-option
              value="melding"
              label="Melding"
              initial-selected="true"
            />
            <oip-select-option value="klacht" label="Klacht" />
          </oip-filter-select>
          <oip-filter-select name="datum" label="Datum">
            <oip-select-option value="week" label="Afgelopen week" />
            <oip-select-option value="maand" label="Afgelopen maand" />
            <oip-select-option value="jaar" label="Afgelopen jaar" />
          </oip-filter-select>
        </oip-sig-bar-test>
        <oip-sig-summary-test />
      </oip-sig-root-test>
    </form>
  ),
};

/** Radio (single-select) group alongside checkbox groups. */
export const WithRadioGroup: StoryObj = {
  render: () => (
    <form method="GET" action="">
      <oip-sig-root-test>
        <oip-sig-bar-test>
          <oip-filter-select name="status" label="Status">
            <oip-select-option
              value="open"
              label="Open"
              initial-selected="true"
            />
            <oip-select-option value="in-behandeling" label="In behandeling" />
            <oip-select-option value="afgerond" label="Afgerond" />
          </oip-filter-select>
          <oip-filter-select
            name="datum"
            label="Datum (kies één)"
            multiple="false"
          >
            <oip-select-option value="week" label="Afgelopen week" />
            <oip-select-option value="maand" label="Afgelopen maand" />
            <oip-select-option value="jaar" label="Afgelopen jaar" />
          </oip-filter-select>
        </oip-sig-bar-test>
        <oip-sig-summary-test />
      </oip-sig-root-test>
    </form>
  ),
};
