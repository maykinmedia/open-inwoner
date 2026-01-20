import { Meta, StoryObj } from '@storybook/preact';
import Badge, { BadgeProps } from './Badge';

const meta: Meta<typeof Badge> = {
  title: 'Components/Badge',
  component: Badge,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
A Badge component for displaying status labels, tags, or indicators.

**Web Component:** \`<oip-badge>\`

**Props:**
- \`label\`: The text to display in the badge
- \`variant\`: The color variant (default, success, warning, error, info)

**Web Component Usage:**
\`\`\`html
<oip-badge label="Nieuw" variant="success"></oip-badge>
<oip-badge label="In behandeling" variant="warning"></oip-badge>
<oip-badge label="Afgewezen" variant="error"></oip-badge>
\`\`\`
`,
      },
    },
  },
};
export default meta;

type Story = StoryObj<BadgeProps>;

export const Default: Story = {
  args: {
    label: 'Label',
    variant: 'default',
  },
};

export const Success: Story = {
  args: {
    label: 'Nieuw',
    variant: 'success',
  },
  parameters: {
    docs: {
      description: {
        story: 'Success variant - used for positive states like "Nieuw" (New).',
      },
    },
  },
};

export const Warning: Story = {
  args: {
    label: 'In behandeling',
    variant: 'warning',
  },
  parameters: {
    docs: {
      description: {
        story: 'Warning variant - used for pending or attention-needed states.',
      },
    },
  },
};

export const Error: Story = {
  args: {
    label: 'Afgewezen',
    variant: 'error',
  },
  parameters: {
    docs: {
      description: {
        story: 'Error variant - used for negative or rejected states.',
      },
    },
  },
};

export const Info: Story = {
  args: {
    label: 'Informatie',
    variant: 'info',
  },
  parameters: {
    docs: {
      description: {
        story: 'Info variant - used for informational states.',
      },
    },
  },
};

export const AllVariants: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
      <Badge label="Default" variant="default" />
      <Badge label="Nieuw" variant="success" />
      <Badge label="In behandeling" variant="warning" />
      <Badge label="Afgewezen" variant="error" />
      <Badge label="Informatie" variant="info" />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'All badge variants displayed together.',
      },
    },
  },
};
