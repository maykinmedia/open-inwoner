import React from 'react';
import { Meta, StoryObj } from '@storybook/react';
import './HomepagePluginSection';

interface HomepagePluginSectionProps {
  title?: string;
  nextUrl?: string;
  nextUrlLabel?: string;
  showIndicator?: boolean;
}

const meta: Meta<HomepagePluginSectionProps> = {
  title: 'WebComponents/HomepagePluginSection',
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
The homepage plugin section web component. This section typically consist of a surrounding section element and contains a headergroup with a title defined bij the CMS. A headergroup can have notifications in the shape of a red dot.

**Props:**
- \`title\`: Heading of the section.
- \`nextUrl\`: Optional URL for the "next" link.
- \`nextUrlLabel\`: Label for the "next" link.
- \`showIndicator\`: Boolean to show notification indicator.
        `,
      },
    },
  },
};

export default meta;

type Story = StoryObj<HomepagePluginSectionProps>;

export const Default: Story = {
  args: {
    title: 'Mijn plugin sectie',
    nextUrl: '/volgende-pagina',
    nextUrlLabel: 'Lees verder',
    showIndicator: false,
  },
  render: ({ title, nextUrl, nextUrlLabel, showIndicator }) =>
    React.createElement('oip-homepage-plugin-section', {
      title,
      'next-url': nextUrl,
      'next-url-label': nextUrlLabel,
      'show-indicator': showIndicator,
    }),
};

export const WithIndicator: Story = {
  args: {
    title: 'Openstaande acties',
    nextUrl: '',
    nextUrlLabel: '',
    showIndicator: true,
  },
  render: ({ title, nextUrl, nextUrlLabel, showIndicator }) =>
    React.createElement('oip-homepage-plugin-section', {
      title,
      'next-url': nextUrl,
      'next-url-label': nextUrlLabel,
      'show-indicator': showIndicator,
    }),
};
