import {
  WEB_COMPONENT_NAME as ACTION_LIST,
  IActionListProps,
} from '@react/components/ActionList';
import {
  KVKBranchSelectorProps,
  WEB_COMPONENT_NAME as KVK_BRANCH_SELECTOR,
} from '@react/components/KVKBranchSelector';
import {
  WEB_COMPONENT_NAME as MATERIAL_ICON,
  MaterialIconProps,
} from '@react/components/MaterialIcon';
import {
  WEB_COMPONENT_NAME as SIDE_NAV,
  SideNavProps,
} from '@react/components/SideNav';
import { KebabCasedProperties } from 'type-fest';

interface WebComponentRegistery {
  [ACTION_LIST]: KebabCasedProperties<IActionListProps>;
  [SIDE_NAV]: KebabCasedProperties<SideNavProps>;
  [KVK_BRANCH_SELECTOR]: KebabCasedProperties<KVKBranchSelectorProps>;
  [MATERIAL_ICON]: KebabCasedProperties<MaterialIconProps>;
}

/**
 * Type declarations for custom web components
 */

declare global {
  namespace preact.JSX {
    interface IntrinsicElements extends WebComponentRegistery {}
  }
}

export {};
