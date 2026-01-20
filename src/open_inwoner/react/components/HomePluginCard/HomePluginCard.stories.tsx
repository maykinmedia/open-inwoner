import '@open-inwoner/design-tokens/dist/css/index.css';
import type { Meta, StoryObj } from '@storybook/preact';
import { withLoader } from '@react/lib/decorators/storybook';
import { HOME_PLUGIN_CARD_ITEM_DEFINITION, HomepageCardTypes } from '.';
import './HomePluginCard';
import HomePluginCard from './HomePluginCard';

const meta: Meta<HomepageCardTypes> = {
  title: 'Components/HomePluginCardItem',
  component: HomePluginCard,
  parameters: {
    layout: 'padded',
  },
};

export default meta;

type Story = StoryObj<HomepageCardTypes>;

export const Default: Story = {
  args: {
    description: 'Identificatie: 100-100-100',
    identificatie: 'abcdef',
    detailUrl: '/mijn-aanvragen/1/abcdef/status/',
    title: 'TEST',
    renderAsHeading: false,
  },
};

export const RenderedWithHeading: Story = {
  args: {
    description: 'Beschrijving over de melding openbare ruimte',
    identificatie: 'abcdef',
    detailUrl: '/mijn-aanvragen/1/abcdef/status/',
    title: 'Melding openbare ruimte',
    renderAsHeading: true,
  },
};

export const WithDateAndTime: Story = {
  args: {
    address: 'Abc-straat 10, Den Broek',
    date: '11 november 2011 om 11:11',
    identificatie: 'abcdef',
    detailUrl: '/mijn-aanvragen/1/abcdef/status/',
    title: 'Melding openbare ruimte',
  },
};

export const ForLocation: Story = {
  args: {
    description: 'Hoofkantoor',
    identificatie: 'abcdef',
    detailUrl: '/mijn-aanvragen/1/abcdef/status/',
    renderAsHeading: true,
    title: 'Melding openbare ruimte',
  },
};

export const AsWebComponent: Story = {
  args: {
    description: 'Melding openbare ruimte',
    identificatie: 'abcdef',
    detailUrl: '/mijn-aanvragen/1/abcdef/status/',
    title: 'Test',
  },
  decorators: [withLoader(HOME_PLUGIN_CARD_ITEM_DEFINITION.tagName)],
  render: ({ description, identificatie, detailUrl, title }) => (
    <oip-home-plugin-card
      title={title}
      description={description}
      identificatie={identificatie}
      detail-url={detailUrl}
      render-as-heading={false}
    />
  ),
};
