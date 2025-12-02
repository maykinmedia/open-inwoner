/**
 * Web component configuration
 *
 * This is the single source of truth for the SideNav component.
 * The central registry is built from these definitions.
 */
import { WebComponentDefinition } from '@react/lib/web-component';
import type { SideNavProps } from './SideNav';

export const WEB_COMPONENT_NAME = 'side-navigation' as const;

export const SIDE_NAV_DEFINITION: WebComponentDefinition<
  'side-navigation',
  SideNavProps
> = {
  tagName: 'side-navigation',
  propNames: ['items', 'itemsId'],
  options: { shadow: false },
  importer: () => import('./SideNav'),
};
