import React from 'react';
import { Meta, StoryObj } from '@storybook/react';
import './ZakenPluginZaakItem';

interface ZaakItemProps {
  description?: string;
  identificatie?: string;
  detailUrl?: string;
}

const meta: Meta<ZaakItemProps> = {
  title: 'WebComponents/ZakenPluginZaakItem',
  parameters: {
    layout: 'padded',
  },
};

export default meta;

type Story = StoryObj<ZaakItemProps>;

export const Default: Story = {
  args: {
    description: 'Melding openbare ruimte',
    identificatie: 'abcdef',
    detailUrl: '/mijn-aanvragen/1/abcdef/status/',
  },
  render: ({ description, identificatie, detailUrl }) =>
    React.createElement('oip-zaken-plugin-zaak-item', {
      description,
      identificatie,
      'detail-url': detailUrl,
    }),
};
