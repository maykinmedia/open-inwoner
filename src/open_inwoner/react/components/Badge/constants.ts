import { WebComponentDefinition } from '@react/lib/web-component';
import type { BadgeProps } from './Badge';

export const OIP_BADGE_DEFINITION: WebComponentDefinition<
  'oip-badge',
  BadgeProps
> = {
  tagName: 'oip-badge',
  propNames: ['label', 'variant'],
  options: { shadow: false },
  importer: () => import('./Badge'),
};
