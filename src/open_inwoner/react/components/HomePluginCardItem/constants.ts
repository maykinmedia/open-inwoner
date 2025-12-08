/**
 * Web component configuration
 *
 * This is the single source of truth for the HomePluginCardItem component.
 * The central registry is built from these definitions.
 */
import { WebComponentDefinition } from '@react/lib/web-component';
import type { HomepageCardTypes } from '.';

export const HOME_PLUGIN_CARD_ITEM_DEFINITION: WebComponentDefinition<
  'oip-homepage-plugin-card',
  HomepageCardTypes
> = {
  tagName: 'oip-homepage-plugin-card',
  propNames: [
    'description',
    'identificatie',
    'detailUrl',
    'date',
    'address',
    'renderAsHeading',
  ],
  options: { shadow: false, i18n: false },
  importer: () => import('./HomePluginCardItem'),
};
