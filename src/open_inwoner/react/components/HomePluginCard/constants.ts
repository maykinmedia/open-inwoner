import { WebComponentDefinition } from '@react/lib/web-component';
import type { HomepageCardTypes } from '.';

export const HOME_PLUGIN_CARD_ITEM_DEFINITION: WebComponentDefinition<
  'oip-home-plugin-card',
  HomepageCardTypes
> = {
  tagName: 'oip-home-plugin-card',
  propNames: [
    'description',
    'identificatie',
    'detailUrl',
    'date',
    'address',
    'renderAsHeading',
  ],
  options: { shadow: false, i18n: false },
  importer: () => import('./HomePluginCard'),
};
