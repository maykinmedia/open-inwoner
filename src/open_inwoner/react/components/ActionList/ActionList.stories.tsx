import { withLoader } from '@react/lib/decorators/storybook';
import type { Meta, StoryObj } from '@storybook/preact-vite';
import { ActionList, IActionListProps } from '.';
import { factoryActions } from '../Action';

const meta: Meta<typeof ActionList> = {
  title: 'Components/ActionList (Web Component Only)',
  component: ActionList,
  decorators: [withLoader('oip-action-list', 'oip-action')],
  tags: ['Shadow DOM'],
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
A slot-only wrapper for \`oip-action\` items. Use this web component to group actions into a list.

**Slots:**

- \`default\`: The slot where the \`oip-action\` components are placed.

**Usage:**
\`\`\`html
<oip-action-list>
  <oip-action title="Mijn Zaken" message="Er is een nieuwe zaak" action-url="/cases"></oip-action>
  <oip-action title="Mijn Vragen" message="Er is een antwoord op de vraag" action-url="/mijn-vragen"></oip-action>
</oip-action-list>
\`\`\`
`,
      },
    },
  },
};
export default meta;

type Story = StoryObj<IActionListProps>;

const mockActions = factoryActions();

/**
 * Default list of actions rendered as web components.
 */
export const Default: Story = {
  name: 'Default',
  render: () => (
    <oip-action-list>
      {mockActions.map((x) => (
        <oip-action
          action-url={x.actionUrl}
          message={x.message}
          title={x.title}
        />
      ))}
    </oip-action-list>
  ),
};

/**
 * ActionList with no children — renders an empty slot.
 */
export const Empty: Story = {
  name: 'Empty',
  render: () => <oip-action-list />,
};
