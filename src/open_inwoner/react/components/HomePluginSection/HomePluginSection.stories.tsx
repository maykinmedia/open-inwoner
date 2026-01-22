import type { Meta, StoryObj } from '@storybook/preact-vite';

import { withLoader } from '@react/lib/decorators/storybook';

import {
  HOMEPAGE_PLUGIN_SECTION_DEFINITION,
  HomePluginSection,
  type IHomePluginSectionProps,
} from '.';
import {
  HOME_PLUGIN_CARD_ITEM_DEFINITION,
  HomePluginCard,
} from '../HomePluginCard';

type Story = StoryObj<IHomePluginSectionProps>;

const meta: Meta<IHomePluginSectionProps> = {
  title: 'Components/HomePluginSection',
  component: HomePluginSection,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
The homepage plugin section web component. This section typically consists of a surrounding section element and contains a headergroup with a title defined by the CMS. A headergroup can have notifications in the shape of a red dot.

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
};

export const WithIndicator: Story = {
  args: {
    title: 'Mijn plugin sectie',
    nextUrl: '/volgende-pagina',
    nextUrlLabel: 'Lees verder',
    showIndicator: true,
    children: (
      <>
        <HomePluginCard
          title="Aanvraag vergunning"
          description="Uw aanvraag wordt verwerkt"
          detailUrl="/zaken/1"
          identificatie="ZAAK-2024-001"
        />
        <HomePluginCard
          title="Melding openbare ruimte"
          description="Wij hebben uw melding ontvangen"
          detailUrl="/zaken/2"
          identificatie="ZAAK-2024-002"
        />
        <HomePluginCard
          title="Bezwaar parkeerboete"
          detailUrl="/zaken/3"
          identificatie="ZAAK-2024-003"
        />
        <HomePluginCard
          title="Paspoort aanvraag"
          detailUrl="/zaken/4"
          identificatie="ZAAK-2024-004"
        />
      </>
    ),
  },
};

export const AsWebComponent: Story = {
  decorators: [
    withLoader(HOMEPAGE_PLUGIN_SECTION_DEFINITION.tagName),
    withLoader(HOME_PLUGIN_CARD_ITEM_DEFINITION.tagName),
  ],
  args: {
    title: 'Openstaande acties',
    showIndicator: true,
  },
  render: ({ title, nextUrl, nextUrlLabel, showIndicator }) => (
    <oip-home-plugin-section
      title={title}
      next-url={nextUrl}
      next-url-label={nextUrlLabel}
      show-indicator={showIndicator}
      columns={2}
    >
      <oip-home-plugin-card
        title="Aanvraag bouwvergunning"
        description="Uw aanvraag voor een bouwvergunning is in behandeling"
        identificatie="ZAAK-2024-0123"
        detail-url="/zaken/0123"
        render-as-heading={false}
      />
      <oip-home-plugin-card
        title="Melding straatverlichting"
        description="De kapotte straatverlichting wordt deze week gerepareerd"
        identificatie="MELDING-2024-0456"
        detail-url="/meldingen/0456"
        render-as-heading={false}
      />
      <oip-home-plugin-card
        title="Paspoort aanvraag"
        description="Uw paspoort ligt klaar voor ophalen"
        identificatie="DOC-2024-0789"
        detail-url="/documenten/0789"
        render-as-heading={false}
      />
      <oip-home-plugin-card
        title="Parkeervergunning verlenging"
        description="Uw parkeervergunning verloopt over 2 weken"
        identificatie="VERG-2024-0321"
        detail-url="/vergunningen/0321"
        render-as-heading={false}
      />
    </oip-home-plugin-section>
  ),
};
