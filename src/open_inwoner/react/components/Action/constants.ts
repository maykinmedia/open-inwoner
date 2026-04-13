import { WebComponentDefinition } from '@react/lib/web-component';
import { createStyleSheets } from '@react/lib/css';
import { IActionProps } from './Action';
import style from './Action.scss?inline';

export const ACTION_DEFINITION: WebComponentDefinition<
  'oip-action',
  IActionProps
> = {
  tagName: 'oip-action',
  propNames: ['title', 'message', 'actionUrl'],
  options: {
    shadow: true,
    adoptedStyleSheets: createStyleSheets(style),
    internals: { role: 'listitem' },
  },
  importer: () => import('./Action'),
};
