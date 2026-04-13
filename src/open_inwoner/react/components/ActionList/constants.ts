import { WebComponentDefinition } from '@react/lib/web-component';
import { createStyleSheets } from '@react/lib/css';
import type { IActionListProps } from './ActionList';
import style from './ActionList.scss?inline';

export const ACTION_LIST_DEFINITION: WebComponentDefinition<
  'oip-action-list',
  IActionListProps
> = {
  tagName: 'oip-action-list',
  propNames: [],
  options: {
    shadow: true,
    adoptedStyleSheets: createStyleSheets(style),
    internals: { role: 'list' },
  },
  importer: () => import('./ActionList'),
};
