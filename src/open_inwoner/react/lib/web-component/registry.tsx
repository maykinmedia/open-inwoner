import { WEB_COMPONENT_NAME as ACTION_LIST } from '@react/components/ActionList/constants';
import { WEB_COMPONENT_NAME as KVK_BRANCH_SELECTOR } from '@react/components/KVKBranchSelector/constants';
import { WEB_COMPONENT_NAME as MATERIAL_ICON } from '@react/components/MaterialIcon/constants';
import { WEB_COMPONENT_NAME as SIDE_NAV } from '@react/components/SideNav/constants';
import {
  performancePlugin,
  silentErrorPlugin,
  skeletonPlugin,
} from './plugins';
import type { WebComponentPlugin } from './types';

/**
 * Object containing key-value pairs of the webcomponent name (key)
 * and import location of the `loadWebComponent` function.
 *
 * These are the exact path's, otherwise lazy loading won't work.
 *
 * NOTE: Make sure to add the web component props to `web-components.d.ts`.
 * This allows the jsx engine to recognize the element and props.
 */
export const wcRegistry = {
  [ACTION_LIST]: () => import('@react/components/ActionList/ActionList'),
  [SIDE_NAV]: () => import('@react/components/SideNav/SideNav'),
  [KVK_BRANCH_SELECTOR]: () =>
    import('@react/components/KVKBranchSelector/KVKBranchSelector'),
  [MATERIAL_ICON]: () => import('@react/components/MaterialIcon/MaterialIcon'),
};

/**
 * Global plugins that run for all web components
 */
export const wcPluginRegistry: WebComponentPlugin[] = [
  silentErrorPlugin,
  skeletonPlugin,
  // @ts-expect-error
  ...(window.IS_DEV ? [performancePlugin] : []),
];
