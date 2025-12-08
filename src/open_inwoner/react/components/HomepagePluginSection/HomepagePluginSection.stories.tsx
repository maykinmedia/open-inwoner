import '@open-inwoner/design-tokens/dist/css/index.css';
import type { Meta, StoryObj } from '@storybook/preact';
import { withLoader } from '@react/lib/decorators/storybook';
import { HOMEPAGE_PLUGIN_SECTION_DEFINITION } from '.';
import { HomepagePluginSection } from '../HomePluginCardItem';

interface HomepagePluginSectionProps {
  title?: string;
  nextUrl?: string;
  nextUrlLabel?: string;
  showIndicator?: boolean;
}

type Story = StoryObj<HomepagePluginSectionProps>;

const meta: Meta<HomepagePluginSectionProps> = {
  title: 'WebComponents/HomepagePluginSection',
  component: HomepagePluginSection,
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

export const Default: Story = {
  args: {
    title: 'Mijn plugin sectie',
    nextUrl: '/volgende-pagina',
    nextUrlLabel: 'Lees verder',
    showIndicator: false,
  },
  render: ({ title, nextUrl, nextUrlLabel, showIndicator }) =>
    `<oip-homepage-plugin-section title="${title}" next-url="${nextUrl}" next-url-label="${nextUrlLabel}" show-indicator="${showIndicator}"></oip-homepage-plugin-section>` as any,
};

export const AsWebComponent: Story = {
  decorators: [withLoader(HOMEPAGE_PLUGIN_SECTION_DEFINITION.tagName)],
  args: {
    title: 'Openstaande acties',
    nextUrl: '',
    nextUrlLabel: '',
    showIndicator: true,
  },
  render: ({ title, nextUrl, nextUrlLabel, showIndicator }) => (
    <oip-homepage-plugin-section
      title={title}
      next-url={nextUrl}
      next-url-label={nextUrlLabel}
      show-indicator={showIndicator}
      columns={2}
    >
      <div>I am a card</div>
    </oip-homepage-plugin-section>
  ),
};
