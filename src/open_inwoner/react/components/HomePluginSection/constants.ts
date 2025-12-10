import { WebComponentDefinition } from '@react/lib/web-component';
import { IHomePluginSectionProps } from './HomePluginSection';

export const HOME_PLUGIN_SECTION_DEFINITION: WebComponentDefinition<
  'oip-home-plugin-section',
  IHomePluginSectionProps
> = {
  tagName: 'oip-home-plugin-section',
  propNames: [],
  options: { shadow: false, i18n: false },
  importer: () => import('./HomePluginSection'),
};
