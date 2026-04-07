import { withLoader } from '@react/lib/decorators';
import { waitForCustomElement } from '@react/lib/testing';
import type { Meta, StoryObj } from '@storybook/preact-vite';
import { expect } from 'storybook/test';

import { PARAGRAPH_DEFINITION, type IParagraphProps } from '.';

const meta: Meta<IParagraphProps> = {
  title: 'Components / Paragraph',
  decorators: [withLoader(PARAGRAPH_DEFINITION.tagName)],
  tags: ['Shadow DOM', 'Web Component'],
  parameters: {
    layout: 'padded',
  },
};

export default meta;

type Story = StoryObj<typeof meta>;

/**
 * Default paragraph rendering.
 */
export const Default: Story = {
  render: () => (
    <nl-paragraph>Pa's wijze lynx bezag vroom het fikse aquaduct.</nl-paragraph>
  ),
  play: async ({ canvasElement, step }) => {
    const paragraph = await waitForCustomElement(canvasElement, 'nl-paragraph');
    const sr = paragraph.shadowRoot!;

    await step('renders paragraph element in shadow DOM', async () => {
      await expect(sr.querySelector('p')).toBeInTheDocument();
    });
  },
};

/**
 * Lead paragraph, bedoeld als inleidende tekst met meer nadruk.
 */
export const Lead: Story = {
  render: () => (
    <nl-paragraph purpose="lead">
      Dit is een lead paragraph, bedoeld als inleidende tekst met meer nadruk.
    </nl-paragraph>
  ),
  play: async ({ canvasElement, step }) => {
    const paragraph = await waitForCustomElement(canvasElement, 'nl-paragraph');
    const sr = paragraph.shadowRoot!;

    await step('renders nl-paragraph--lead class', async () => {
      await expect(sr.querySelector('p')).toHaveClass('nl-paragraph--lead');
    });
  },
};

/**
 * Muted paragraph met de OIP-specifieke modifier class.
 */
export const Muted: Story = {
  render: () => (
    <nl-paragraph class-name="nl-paragraph--oip-muted">
      Dit is een muted paragraph met de OIP-specifieke modifier class.
    </nl-paragraph>
  ),
  play: async ({ canvasElement, step }) => {
    const paragraph = await waitForCustomElement(canvasElement, 'nl-paragraph');
    const sr = paragraph.shadowRoot!;

    await step('renders nl-paragraph--oip-muted class', async () => {
      await expect(sr.querySelector('p')).toHaveClass(
        'nl-paragraph--oip-muted'
      );
    });
  },
};
