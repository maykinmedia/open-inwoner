import { Meta, StoryObj } from '@storybook/preact';
import { Example, IExampleProps, IExampleDataProps, loader } from '.';
import { withLoader } from '@react/lib/decorators/storybook';

const meta: Meta<typeof Example> = {
  title: 'Components/Example',
  component: Example,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
The Example component displays the base of a OIP web component.

This Component should be the baseline of new components.

**Props:**
- \`data\`: Array of data - used only for Preact components
- \`dataId\`: String to receive the data - used only for web components

**Item Structure:**
- \`title\`: Item title
- \`description\`: Item description/description
- \`data_url\`: A example URL
`,
      },
    },
  },
};
export default meta;

type Story = StoryObj<IExampleProps>;

const mockDataWithItems: IExampleDataProps[] = [
  {
    title: 'Complete your profile',
    description: 'Please fill in your personal information to continue.',
    data_url: '/profile',
  },
  {
    title: 'Document uploaded successfully',
    description: 'Your document has been received and is being processed.',
    data_url: '/documents',
  },
  {
    title: 'Payment failed',
    description:
      'Your recent payment could not be processed. Please update your payment method.',
    data_url: '/payment',
  },
  {
    title: 'New description received',
    description: 'You have a new description from the municipality.',
    data_url: '/descriptions',
  },
];

export const Default: Story = {
  name: 'Default with Items',
  args: {
    data: mockDataWithItems,
  },
  parameters: {
    docs: {
      description: {
        story: 'Default Example.',
      },
    },
  },
};

export const Empty: Story = {
  name: 'Empty List',
  args: {
    data: [],
  },
  parameters: {
    docs: {
      description: {
        story: 'Example with no data - so nothing is rendered.',
      },
    },
  },
};

/**
 * Rendered as webcomponent
 */
export const AsWebComponent: Story = {
  args: { dataId: 'test-id' },
  decorators: withLoader(loader),
  render: ({ dataId }) => (
    <>
      <script type="application/json" id={dataId}>
        {JSON.stringify(mockDataWithItems)}
      </script>
      {/* @ts-expect-error should be included in `web-components.d.ts` */}
      <oip-example data-id={dataId} />
    </>
  ),
};
