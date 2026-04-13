import { withLoader } from '@react/lib/decorators';
import type { Meta, StoryObj } from '@storybook/preact-vite';
import { Action, ACTION_DEFINITION, factoryAction, type IActionProps } from '.';

const meta: Meta<typeof Action> = {
  title: 'Web Components / Action',
  component: Action,
  decorators: [withLoader(ACTION_DEFINITION.tagName)],
  tags: ['Shadow DOM'],
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
A single action item that links the user to a relevant page. Renders a title and message inside a Den Haag \`ActionSingle\` link.

**Props:**
- \`title\`: The section name (e.g. "Mijn Zaken")
- \`message\`: A short description of the action
- \`actionUrl\`: The URL the link navigates to

**Usage:**
\`\`\`tsx
<oip-action title="Mijn Zaken" message="Er is een nieuwe zaak" action-url="/cases"></oip-action>
\`\`\`
`,
      },
    },
  },
};
export default meta;

type Story = StoryObj<IActionProps>;

export const Default: Story = {
  name: 'Default',
  args: factoryAction(),
  render: (args) => (
    <oip-action
      action-url={args.actionUrl}
      message={args.message}
      title={args.title}
    />
  ),
};

/**
 * Action rendered without a title — only the message is shown.
 */
export const NoTitle: Story = {
  name: 'No Title',
  args: factoryAction({ title: '' }),
  render: (args) => (
    <oip-action action-url={args.actionUrl} message={args.message} title="" />
  ),
};

/**
 * Action rendered without a message — only the title is shown.
 */
export const NoMessage: Story = {
  name: 'No Message',
  args: factoryAction({ message: '' }),
  render: (args) => (
    <oip-action action-url={args.actionUrl} message="" title={args.title} />
  ),
};
