import { withLoader } from '@react/lib/decorators/storybook';
import { Meta, StoryObj } from '@storybook/preact-vite';
import { DATASUMMARY_DEFINITION } from '.';
import DataSummary from './DataSummary';

const meta: Meta<typeof DataSummary> = {
  title: 'Components/DataSummary',
  component: DataSummary,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
DataSummary is a pure React component that renders a list of title and detail pairs using the Den Haag design system. It accepts an array of items and displays them as a styled description list.

**Features:**
- Responsive design following Den Haag standards
- Built on @gemeente-denhaag/descriptionlist

**Props:**
- \`items\`: Array of ListItem objects with label and value.
        `,
      },
    },
  },
};
export default meta;

type Story = StoryObj<typeof meta>;

const MOCK_DATA_SUMMARY_DATA = [
  { label: 'Status', value: 'Nieuw' },
  { label: 'Ingediend op', value: '5 Juni 2025' },
  { label: 'Vraagnummer', value: 'AB123' },
  { label: 'Contact gehad via', value: 'Contactformulier' },
];

export const Default: Story = {
  name: 'Default',
  args: {
    items: MOCK_DATA_SUMMARY_DATA,
  },
};

export const AsWebComponent: Story = {
  args: { itemsId: 'DataSummary-test-data' },
  decorators: [withLoader(DATASUMMARY_DEFINITION.tagName)],
  render: ({ itemsId }) => (
    <>
      <script type="application/json" id={itemsId}>
        {JSON.stringify(MOCK_DATA_SUMMARY_DATA)}
      </script>
      <oip-data-summary items-id={itemsId} />
    </>
  ),
};
