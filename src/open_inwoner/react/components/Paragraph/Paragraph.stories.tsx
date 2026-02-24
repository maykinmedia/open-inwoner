import type { Meta, StoryObj } from '@storybook/preact-vite';
import { withLoader } from '@react/lib/decorators/storybook';
import { PARAGRAPH_DEFINITION, type IParagraphProps } from '.';
import Paragraph from './Paragraph';

// TODO: once PR #2310 (shadow DOM / testing utils) is merged:
// - add tags: ['Shadow DOM', 'Web Component']
// - move decorators to meta level
// - add play functions using waitForCustomElement and shadowWithin from @react/lib/testing

type Story = StoryObj<IParagraphProps & { text: string }>;

const meta: Meta<IParagraphProps & { text: string }> = {
  title: 'Components / Paragraph',
  component: Paragraph,
  decorators: [withLoader(PARAGRAPH_DEFINITION.tagName)],
  parameters: {
    layout: 'padded',
  },
  argTypes: {
    text: {
      name: 'Tekst',
      control: 'text',
    },
  },
  args: {
    text: "Pa's wijze lynx bezag vroom het fikse aquaduct.",
  },
};

export default meta;

export const Default: Story = {
  render: ({ text }) => <nl-paragraph>{text}</nl-paragraph>,
};

export const Lead: Story = {
  args: {
    text: 'Dit is een lead paragraph, bedoeld als inleidende tekst met meer nadruk.',
  },
  render: ({ text }) => <nl-paragraph purpose="lead">{text}</nl-paragraph>,
};

export const Muted: Story = {
  args: {
    text: 'Dit is een muted paragraph met de OIP-specifieke modifier class.',
  },
  render: ({ text }) => (
    <nl-paragraph class-name="nl-paragraph--oip-muted">{text}</nl-paragraph>
  ),
};
