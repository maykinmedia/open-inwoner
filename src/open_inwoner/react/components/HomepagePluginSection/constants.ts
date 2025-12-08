/**
 * Loading Home page plugin section constants
 *
 * This component doesn't expose any props to the outside.
 */
import { WebComponentDefinition } from '@react/lib/web-component';
import { IHomepagePluginSectionProps } from './HomepagePluginSection';

export const HOMEPAGE_PLUGIN_SECTION_DEFINITION: WebComponentDefinition<
  'oip-homepage-plugin-section',
  IHomepagePluginSectionProps
> = {
  tagName: 'oip-homepage-plugin-section',
  propNames: [],
  options: { shadow: false, i18n: false },
  importer: () => import('./HomepagePluginSection'),
};
