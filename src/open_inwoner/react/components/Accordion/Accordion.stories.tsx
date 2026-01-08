import { withLoader } from '@react/lib/decorators/storybook';
import { Meta, StoryObj } from '@storybook/preact';
import { ACCORDION_DEFINITION, Accordion, IAccordionProps } from '.';
import { ActionList } from '../ActionList';

const meta: Meta<typeof Accordion> = {
  title: 'Components/Accordion',
  component: Accordion,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
The Accordion component is a collapsible disclosure widget that shows and hides content using the native HTML details/summary elements.

This component provides an accessible way to organize and reveal content on demand, with support for custom icons and styling.

**Props:**
- \`title\`: The title of the accordion
- \`subtitle\`: The subtitle of the accordion
- \`initialOpen\`: Render open accordion
- \`icon\`: Define custom icon
- \`children\`: The disclosed element
`,
      },
    },
  },
};
export default meta;

type Story = StoryObj<IAccordionProps>;

const MockAccordionChild = ({ children }: any) => (
  <div className="card">
    <p className="card__body">{children ?? 'This Is A Mock Accordion Child'}</p>
  </div>
);

export const Default: Story = {
  name: 'Default',
  args: {
    title: 'Accordion',
    subtitle: 'With a subtitle',
    initialOpen: false,
    icon: 'keyboard_arrow_down',
  },
  argTypes: {
    icon: {
      table: {
        defaultValue: { summary: '"keyboard_arrow_down"' },
      },
    },
    initialOpen: {
      table: {
        defaultValue: { summary: 'false' },
      },
    },
  },
  parameters: {
    docs: {
      description: {
        story: 'Default Accordion with title, subtitle, and child content.',
      },
    },
  },
  render: (args) => {
    return (
      <Accordion {...args}>
        <MockAccordionChild />
      </Accordion>
    );
  },
};

export const MultipleChildren: Story = {
  name: 'Multiple Children Accordion',
  args: {
    title: 'Accordion with multiple children',
    subtitle: '8 children found',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Accordion with multiple children (does not have to be wrapped by a container)',
      },
    },
  },
  render: (args) => {
    return (
      <Accordion {...args}>
        {Array.from({ length: 8 }).map((_, i) => (
          <MockAccordionChild>Child: {i + 1}</MockAccordionChild>
        ))}
      </Accordion>
    );
  },
};

export const OnlyTitle: Story = {
  name: 'Only A Title',
  args: {
    title: 'Render with only a title',
  },
  parameters: {
    docs: {
      description: {
        story: 'Accordion can be rendered with only a title',
      },
    },
  },
  render: (args) => {
    return (
      <Accordion {...args}>
        <MockAccordionChild />
      </Accordion>
    );
  },
};

export const OnlySubtitle: Story = {
  name: 'Only A Subtitle',
  args: {
    subtitle: 'Render with only a subtitle',
  },
  parameters: {
    docs: {
      description: {
        story: 'Accordion can be rendered with only a subtitle',
      },
    },
  },
  render: (args) => {
    return (
      <Accordion {...args}>
        <MockAccordionChild />
      </Accordion>
    );
  },
};

export const InitialOpen: Story = {
  name: 'Initial Open',
  args: {
    title: 'Initial open accordion',
    subtitle: 'Render an accordion which renders open',
    initialOpen: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Accordion can be rendered initially open',
      },
    },
  },
  render: (args) => {
    return (
      <Accordion {...args}>
        <MockAccordionChild>I AM OPEN!</MockAccordionChild>
      </Accordion>
    );
  },
};

export const CustomIcon: Story = {
  name: 'Custom Icon',
  args: {
    title: 'Custom icon accordion',
    subtitle: 'Render an accordion with a custom icon',
    icon: 'keyboard_double_arrow_down',
  },
  parameters: {
    docs: {
      description: {
        story: 'Not every accordion has the same icon',
      },
    },
  },
  render: (args) => {
    return (
      <Accordion {...args}>
        <MockAccordionChild>With custom icon</MockAccordionChild>
      </Accordion>
    );
  },
};

export const CombinedWithActionList: Story = {
  name: 'Combined with action list',
  args: {
    title: 'Mijn actie punten',
    subtitle: 'Totaal: 4 openstaande acties',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Not a real world example, but this shows how the accordion works with other components',
      },
    },
  },
  render: (args) => {
    return (
      <Accordion {...args}>
        <ActionList
          actions={[
            {
              action_url: '',
              message: 'Er is een nieuwe zaak toegevoegd',
              title: 'Mijn Zaken',
            },
            {
              action_url: '',
              message: 'Controleer uitkeringen',
              title: 'Mijn Uitkeringen',
            },
            {
              action_url: '',
              message: 'Stel een nieuwe vraag',
              title: 'Mijn Vragen',
            },
            {
              action_url: '',
              message: 'Start nieuwe samenwerking',
              title: 'Mijn Samenwerkingen',
            },
          ]}
        />
      </Accordion>
    );
  },
};

/**
 * Rendered as webcomponent
 */
export const AsWebComponent: Story = {
  args: {
    title: 'Web component accordion',
    subtitle: 'We can render an accordion as a web component',
    initialOpen: false,
  },
  decorators: withLoader(ACCORDION_DEFINITION.tagName),
  render: ({ title, subtitle, initialOpen }) => (
    <oip-accordion title={title} subtitle={subtitle} initial-open={initialOpen}>
      <MockAccordionChild>Accordion as a web component</MockAccordionChild>
    </oip-accordion>
  ),
};
