/**
 * Material Icon constants
 *
 * This is the single source of truth for the MaterialIcon component.
 * The central registry is built from these definitions.
 */
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
