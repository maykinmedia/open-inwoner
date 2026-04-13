import { withLoader } from '@react/lib/decorators';
import type { Meta, StoryObj } from '@storybook/preact-vite';
import { FILTERS_DEFINITION } from './constants';

const filterGroups = [
  {
    name: 'status',
    label: 'Status',
    choices: [
      { label: 'Open', value: 'open' },
      { label: 'In behandeling', value: 'in-behandeling' },
      { label: 'Afgerond', value: 'afgerond' },
      { label: 'Geannuleerd', value: 'geannuleerd' },
    ],
  },
  {
    name: 'categorie',
    label: 'Categorie',
    choices: [
      { label: 'Vraag', value: 'vraag' },
      { label: 'Melding', value: 'melding' },
      { label: 'Klacht', value: 'klacht' },
    ],
  },
  {
    name: 'datum',
    label: 'Datum',
    choices: [
      { label: 'Afgelopen week', value: 'week' },
      { label: 'Afgelopen maand', value: 'maand' },
      { label: 'Afgelopen jaar', value: 'jaar' },
    ],
  },
];

const Composition = ({ dataId }: { dataId: string }) => (
  <oip-filters data-id={dataId}>
    <oip-filter-bar>
      <oip-filter name="status"></oip-filter>
      <oip-filter name="categorie"></oip-filter>
      <oip-filter name="datum"></oip-filter>
    </oip-filter-bar>
    <oip-filter-chips></oip-filter-chips>
  </oip-filters>
);

const meta: Meta = {
  title: 'Components/FiltersClone',
  decorators: [withLoader(FILTERS_DEFINITION.tagName)],
  parameters: { layout: 'padded' },
};

export default meta;

export const Default: StoryObj = {
  render: () => (
    <>
      <script type="application/json" id="filters-data">
        {JSON.stringify({
          filterGroups,
          initialFilterState: { status: [], categorie: [], datum: [] },
        })}
      </script>
      <Composition dataId="filters-data" />
    </>
  ),
};

export const WithActiveFilters: StoryObj = {
  render: () => (
    <>
      <script type="application/json" id="filters-active">
        {JSON.stringify({
          filterGroups,
          initialFilterState: {
            status: ['open', 'in-behandeling'],
            categorie: ['melding'],
            datum: [],
          },
        })}
      </script>
      <Composition dataId="filters-active" />
    </>
  ),
};
