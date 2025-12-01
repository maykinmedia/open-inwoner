import {
  ACTION_LIST_DEFINITION,
  WEB_COMPONENT_NAME as ACTION_LIST_NAME,
} from '@react/components/ActionList/constants';
import {
  KVK_BRANCH_SELECTOR_DEFINITION,
  WEB_COMPONENT_NAME as KVK_BRANCH_SELECTOR_NAME,
} from '@react/components/KVKBranchSelector/constants';
import {
  MATERIAL_ICON_DEFINITION,
  WEB_COMPONENT_NAME as MATERIAL_ICON_NAME,
} from '@react/components/MaterialIcon/constants';
import {
  SIDE_NAV_DEFINITION,
  WEB_COMPONENT_NAME as SIDE_NAV_NAME,
} from '@react/components/SideNav/constants';
import type { KebabCasedProperties } from 'type-fest';

import type { IActionListProps } from '@react/components/ActionList';
import type { KVKBranchSelectorProps } from '@react/components/KVKBranchSelector';
import type { MaterialIconProps } from '@react/components/MaterialIcon';
import type { SideNavProps } from '@react/components/SideNav';

/**
 * Web component registry
 * Maps tag names to their definitions
 */
export const WEB_COMPONENT_REGISTRY = {
  [ACTION_LIST_NAME]: ACTION_LIST_DEFINITION,
  [SIDE_NAV_NAME]: SIDE_NAV_DEFINITION,
  [KVK_BRANCH_SELECTOR_NAME]: KVK_BRANCH_SELECTOR_DEFINITION,
  [MATERIAL_ICON_NAME]: MATERIAL_ICON_DEFINITION,
} as const;

/**
 * Valid web component tag names - derived from the registry keys
 */
export type WebComponentTagName = keyof typeof WEB_COMPONENT_REGISTRY;

/**
 * Utility type to map component tag names to their prop types
 * Used for JSX type generation
 */
export type WebComponentProps = {
  [ACTION_LIST_NAME]: IActionListProps;
  [SIDE_NAV_NAME]: SideNavProps;
  [KVK_BRANCH_SELECTOR_NAME]: KVKBranchSelectorProps;
  [MATERIAL_ICON_NAME]: MaterialIconProps;
};
/**
 * JSX Registry - automatically derived from WebComponentProps
 * Maps web component tag names to their kebab-cased prop types
 * This is used in web-components.d.ts to provide JSX typing
 */
export type WebComponentJSXRegistry = {
  [K in keyof WebComponentProps]: KebabCasedProperties<WebComponentProps[K]>;
};
