import { withLoader } from '@react/lib/decorators/storybook';
import { shadowWithin, waitForCustomElement } from '@react/lib/testing';
import type { Meta, StoryObj } from '@storybook/preact-vite';
import { expect, userEvent } from 'storybook/test';
import { Accordion, IAccordionProps } from '.';
import { factoryActions } from '../Action';

const meta: Meta<typeof Accordion> = {
  title: 'Web Components / Accordion',
  component: Accordion,
  decorators: [withLoader('oip-accordion', 'material-icon')],
  tags: ['Shadow DOM', 'Web Component'],
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
The Accordion component is a web-component first component (works as web-component in preact component).
An Accordion is a collapsible disclosure widget that shows and hides content using the native HTML details/summary elements.

This component provides an accessible way to organize and reveal content on demand, with support for custom icons and styling.

**Props:**
- \`initialOpen\`: Render open accordion (default: \`false\` - closed)

**Slots:**

- \`summary\`: The slot where the title (and subtitle) can be placed.
- \`icon\`: The slot for the arrow icon.
- \`default\`: The slot for the disclosed elements.


**Usage:**
\`\`\`html
<oip-accordion initial-open="true">
  <div class="accordion__heading" slot="summary" hidden>
    // Place for a heading
  </div>
  <material-icon name="keyboard_arrow_down" slot="icon" />
  <div>DISCLOSED ELEMENT</div>
<oip-accordion>
\`\`\`
`,
      },
    },
  },
};
export default meta;

type Story = StoryObj<IAccordionProps & { title: string; subtitle: string }>;

const MockAccordionChild = ({ children }: any) => (
  <div style={{ display: 'grid', gap: '1rem' }}>
    <div class="card">
      <p class="card__body">{children} 1</p>
    </div>
    <div class="card">
      <p class="card__body">{children} 2</p>
    </div>
    <div class="card">
      <p class="card__body">{children} 3</p>
    </div>
  </div>
);

/**
 * Default accordion, closed by default.
 */
export const Default: Story = {
  args: {
    title: 'Web component accordion',
    subtitle: 'We can render an accordion as a web component',
    initialOpen: false,
  },
  render: ({ title, subtitle, initialOpen }) => (
    <oip-accordion initial-open={initialOpen}>
      <div class="accordion__heading" slot="summary" hidden>
        <h3 class="utrecht-heading-3">{title}</h3>
        <p class="utrecht-paragraph">{subtitle}</p>
      </div>
      <material-icon name="keyboard_arrow_down" slot="icon" />
      <MockAccordionChild>Accordion as a web component</MockAccordionChild>
    </oip-accordion>
  ),
  play: async ({ canvasElement, step }) => {
    const accordion = await waitForCustomElement(
      canvasElement,
      'oip-accordion'
    );
    const sr = accordion.shadowRoot!;
    const canvas = shadowWithin(accordion);
    const details = canvas.getByRole('group');
    const summary = sr.querySelector('summary')!;

    await step('is closed by default', async () => {
      expect(details).not.toHaveAttribute('open');
    });

    await step('applies CSS classes in shadow DOM', async () => {
      expect(sr.querySelector('details')).toHaveClass('accordion');
      expect(summary).toHaveClass('accordion__summary');
    });

    await step('toggles open and closed on click', async () => {
      await userEvent.click(summary);
      expect(details).toHaveAttribute('open');

      await userEvent.click(summary);
      expect(details).not.toHaveAttribute('open');
    });
  },
};

/**
 * Accordion with `initialOpen` set to `true`, so the content is visible on load.
 */
export const InitialOpen: Story = {
  args: {
    title: 'Web component accordion',
    subtitle: 'We can render an accordion as a web component',
    initialOpen: true,
  },
  render: ({ title, subtitle, initialOpen }) => (
    <oip-accordion initial-open={initialOpen}>
      <div class="accordion__heading" slot="summary" hidden>
        <h3 class="utrecht-heading-3">{title}</h3>
        <p class="utrecht-paragraph">{subtitle}</p>
      </div>
      <material-icon name="keyboard_arrow_down" slot="icon" />
      <MockAccordionChild>Accordion as a web component</MockAccordionChild>
    </oip-accordion>
  ),
  play: async ({ canvasElement }) => {
    const accordion = await waitForCustomElement(
      canvasElement,
      'oip-accordion'
    );
    expect(shadowWithin(accordion).getByRole('group')).toHaveAttribute('open');
  },
};

/**
 * Accordion with a custom icon in the icon slot.
 */
export const WithCustomIcon: Story = {
  args: {
    title: 'Web component accordion',
    subtitle: 'We can render an accordion as a web component',
    initialOpen: true,
  },
  render: ({ title, subtitle, initialOpen }) => (
    <oip-accordion initial-open={initialOpen}>
      <div class="accordion__heading" slot="summary" hidden>
        <h3 class="utrecht-heading-3">{title}</h3>
        <p class="utrecht-paragraph">{subtitle}</p>
      </div>
      <material-icon name="keyboard_double_arrow_down" slot="icon" />
      <MockAccordionChild>With custom icon</MockAccordionChild>
    </oip-accordion>
  ),
};

/**
 * Full composition: oip-accordion wrapping oip-action-list with oip-action children.
 */
export const WCCombinedWithActionList: Story = {
  name: 'Combined with ActionList (Web Component children)',
  decorators: [withLoader('oip-action-list', 'oip-action')],
  args: {
    title: 'Mijn actie punten',
    subtitle: 'Totaal: 4 openstaande acties',
    initialOpen: true,
  },
  parameters: {
    docs: {
      description: {
        story: `Combines all three web components: oip-accordion > oip-action-list > oip-action.`,
      },
    },
  },
  render: (args) => (
    <oip-accordion initial-open={args.initialOpen}>
      <div class="accordion__heading" slot="summary" hidden>
        <h3 class="utrecht-heading-3">{args.title}</h3>
        <p class="utrecht-paragraph">{args.subtitle}</p>
      </div>
      <material-icon name="keyboard_arrow_down" slot="icon" />
      <oip-action-list>
        {factoryActions().map((x) => (
          <oip-action
            action-url={x.actionUrl}
            message={x.message}
            title={x.title}
          />
        ))}
      </oip-action-list>
    </oip-accordion>
  ),
};
