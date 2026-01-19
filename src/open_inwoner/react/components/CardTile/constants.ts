import { WebComponentDefinition } from '@react/lib/web-component';
import type { CardTileTypes } from './types';

export const CARD_TILE_DEFINITION: WebComponentDefinition<
  'oip-card-tile',
  CardTileTypes
> = {
  tagName: 'oip-card-tile',
  propNames: [
    'title',
    'description',
    'identificatie',
    'detailUrl',
    'date',
    'address',
    'keywords',
    'code',
    'createdDate',
    'updatedDate',
    'gepubliceerd',
    'publicatieStartDatum',
    'toegestaneStatussen',
    'prijs',
    'renderAsHeading',
  ],
  options: { shadow: false, i18n: false },
  importer: () => import('./CardTile'),
};
