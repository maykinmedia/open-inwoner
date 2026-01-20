import { WebComponentDefinition } from '@react/lib/web-component';
import type { OipCardProps } from './Card';

export const OIP_CARD_DEFINITION: WebComponentDefinition<
  'oip-card',
  OipCardProps
> = {
  tagName: 'oip-card',
  propNames: [
    'variant',
    // BaseCard props
    'title',
    'description',
    'subtitle',
    'status',
    'href',
    'badgeLabel',
    'badgeVariant',
    'footer',
    // LocationCard props
    'locationName',
    'locationUrl',
    'addressLine1',
    'addressLine2',
    'phoneNumber',
    'email',
  ],
  options: { shadow: false },
  importer: () => import('./Card'),
};
