import { WebComponentDefinition } from '@react/lib/web-component';
import type { MaterialIconProps } from './MaterialIcon';

export const MATERIAL_ICON_DEFINITION: WebComponentDefinition<
  'material-icon',
  MaterialIconProps
> = {
  tagName: 'material-icon',
  propNames: ['name'],
  options: { shadow: false },
  importer: () => import('./MaterialIcon'),
};
