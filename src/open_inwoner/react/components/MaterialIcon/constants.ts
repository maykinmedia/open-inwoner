import { WebComponentDefinition } from '@react/lib/web-component';
import type { MaterialIconProps } from './MaterialIcon';
import { createStyleSheets } from '@react/lib/css';
import styleSheet from './MaterialIcon.scss?inline';

export const MATERIAL_ICON_DEFINITION: WebComponentDefinition<
  'material-icon',
  MaterialIconProps
> = {
  tagName: 'material-icon',
  propNames: ['name'],
  options: {
    shadow: true,
    adoptedStyleSheets: createStyleSheets(styleSheet),
  },
  importer: () => import('./MaterialIcon'),
};
