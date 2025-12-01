/**
 * Web component configuration
 *
 * This is the single source of truth for the ActionList component.
 * The central registry is automatically built from these definitions.
 */

import { WebComponentDefinition } from '@react/lib/web-component';
import type { IActionListProps } from './ActionList';

export const WEB_COMPONENT_NAME = 'action-list' as const;

export const ACTION_LIST_DEFINITION: WebComponentDefinition<IActionListProps> =
  {
    tagName: WEB_COMPONENT_NAME,
    propNames: ['actions', 'actionsId'],
    options: { shadow: false },
    importer: () => import('./ActionList'),
  };
