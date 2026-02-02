import { withLoader } from '@react/lib/decorators/storybook';
import type { Meta, StoryObj } from '@storybook/preact-vite';
import {
  ACTION_LIST_DEFINITION,
  ActionList,
  IActionListProps,
  IActionProps,
} from '.';

const meta: Meta<typeof ActionList> = {
  title: 'Components/ActionList',
  component: ActionList,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
The ActionList component displays a list of user feed items with actions.

This component integrates with the Den Haag Action component and provides a consistent way to display feed items.

**Props:**
- \`actions\`: Array of feed items with type, title, message, status info, and action details

**Item Structure:**
- \`title\`: Item title
- \`message\`: Item description/message
- \`action_url\`: URL for the action link
`,
      },
    },
  },
};
export default meta;

type Story = StoryObj<IActionListProps>;

const mockDataWithItems: IActionProps[] = [
  {
    title: 'Complete your profile',
    message: 'Please fill in your personal information to continue.',
    action_url: '/profile',
  },
  {
    title: 'Document uploaded successfully',
    message: 'Your document has been received and is being processed.',
    action_url: '/documents',
  },
  {
    title: 'Payment failed',
    message:
      'Your recent payment could not be processed. Please update your payment method.',
    action_url: '/payment',
  },
  {
    title: 'New message received',
    message: 'You have a new message from the municipality.',
    action_url: '/messages',
  },
];

export const Default: Story = {
  name: 'Default with Items',
  args: {
    actions: mockDataWithItems,
  },
  parameters: {
    docs: {
      description: {
        story:
          'Default ActionList with various feed items showing different statuses and completion states.',
      },
    },
  },
};

export const Empty: Story = {
  name: 'Empty List',
  args: {
    actions: [],
  },
  parameters: {
    docs: {
      description: {
        story: 'ActionList with no actions - so nothing is rendered.',
      },
    },
  },
};

/**
 * Rendered as webcomponent
 */
export const AsWebComponent: Story = {
  args: { actionsId: 'test-id' },
  decorators: withLoader(ACTION_LIST_DEFINITION.tagName),
  render: ({ actionsId }) => (
    <>
      <script type="application/json" id={actionsId}>
        {JSON.stringify(mockDataWithItems)}
      </script>
      <action-list actions-id={actionsId} is="table" />
    </>
  ),
};
