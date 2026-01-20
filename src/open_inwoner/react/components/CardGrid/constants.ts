import { WebComponentDefinition } from '@react/lib/web-component';
import type { CardGridProps } from './CardGrid';

export const CARD_GRID_DEFINITION: WebComponentDefinition<
  'oip-card-grid',
  CardGridProps
> = {
  tagName: 'oip-card-grid',
  propNames: ['columns'],
  options: { shadow: false, i18n: false },
  importer: () => import('./CardGrid'),
};
