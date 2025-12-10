import { WebComponentDefinition } from '@react/lib/web-component';
import type { IActionListProps } from './ActionList';

export const ACTION_LIST_DEFINITION: WebComponentDefinition<
  'action-list',
  IActionListProps
> = {
  tagName: 'action-list',
  propNames: ['actions', 'actionsId'],
  options: { shadow: false },
  importer: () => import('./ActionList'),
};
