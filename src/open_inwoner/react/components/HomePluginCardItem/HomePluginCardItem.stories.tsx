import '@open-inwoner/design-tokens/dist/css/index.css';
import type { Meta, StoryObj } from '@storybook/preact';
import { withLoader } from '@react/lib/decorators/storybook';
import { HOME_PLUGIN_CARD_ITEM_DEFINITION, HomepageCardTypes } from '.';
import './HomePluginCardItem';
import HomePluginCardItem from './HomePluginCardItem';

const meta: Meta<HomepageCardTypes> = {
  title: 'WebComponents/ZakenPluginZaakItem',
  component: HomePluginCardItem,
  parameters: {
    layout: 'padded',
  },
};

export default meta;

type Story = StoryObj<HomepageCardTypes>;

export const Default: Story = {
  args: {
    description: 'Melding openbare ruimte',
    identificatie: 'abcdef',
    detailUrl: '/mijn-aanvragen/1/abcdef/status/',
  },
  decorators: [withLoader(HOME_PLUGIN_CARD_ITEM_DEFINITION.tagName)],
  render: ({ description, identificatie, detailUrl }) => (
    <oip-homepage-plugin-card
      render-as-h3={false}
      title="TEST"
      description={description}
      identificatie={identificatie}
      detail-url={detailUrl}
      render-as-heading={false}
    />
  ),
};
