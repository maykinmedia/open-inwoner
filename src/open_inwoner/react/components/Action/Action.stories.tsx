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
- \`message\`: A short description of the action
- \`actionUrl\`: The URL the link navigates to
- \`label\`: Text in the status badge. No label means no badge.
- \`status\`: Color of the badge: \`info\`, \`warning\`, \`failure\` or \`success\`. Unknown or empty values fall back to \`info\`.


**Usage:**
\`\`\`tsx
<oip-action message="Documenten nodig voor aanvraag bijzondere bijstand" status="warning" label="U moet een document toevoegen"  action-url="/cases"></oip-action>
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
      label={args.label}
      status={args.status}
    />
  ),
};

/**
 * Action rendered without a message — only the title is shown.
 */
export const Info: Story = {
  name: 'Info',
  args: factoryAction({ label: 'Bekijk actie', status: 'info' }),
  render: (args) => (
    <oip-action
      action-url={args.actionUrl}
      message={args.message}
      label={args.label}
      status={args.status}
    />
  ),
};

export const Warning: Story = {
  name: 'Warning',
  args: factoryAction({
    label: 'U moet een document toevoegen',
    status: 'warning',
  }),
  render: (args) => (
    <oip-action
      action-url={args.actionUrl}
      message={args.message}
      label={args.label}
      status={args.status}
    />
  ),
};

export const Failure: Story = {
  name: 'Failure',
  args: factoryAction({ label: 'Afgewezen', status: 'failure' }),
  render: (args) => (
    <oip-action
      action-url={args.actionUrl}
      message={args.message}
      label={args.label}
      status={args.status}
    />
  ),
};

export const Success: Story = {
  name: 'Success',
  args: factoryAction({ label: 'Afgerond', status: 'success' }),
  render: (args) => (
    <oip-action
      action-url={args.actionUrl}
      message={args.message}
      label={args.label}
      status={args.status}
    />
  ),
};

export const NoLabel: Story = {
  name: 'No Label',
  args: factoryAction({ label: undefined }),
  render: (args) => (
    <oip-action action-url={args.actionUrl} message={args.message} />
  ),
};
