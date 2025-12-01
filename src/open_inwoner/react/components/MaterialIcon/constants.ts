/**
 * Material Icon constants
 *
 * This is the single source of truth for the MaterialIcon component.
 * The central registry built from these definitions.
 */
import { WebComponentDefinition } from '@react/lib/web-component';
import type { MaterialIconProps } from './MaterialIcon';

export const WEB_COMPONENT_NAME = 'material-icon' as const;

export const MATERIAL_ICON_DEFINITION: WebComponentDefinition<MaterialIconProps> =
  {
    tagName: WEB_COMPONENT_NAME,
    propNames: ['name'],
    options: { shadow: false },
    importer: () => import('./MaterialIcon'),
  };
