import { ACTION_LIST_DEFINITION } from '@react/components/ActionList/constants';
import { KVK_BRANCH_SELECTOR_DEFINITION } from '@react/components/KVKBranchSelector/constants';
import { MATERIAL_ICON_DEFINITION } from '@react/components/MaterialIcon/constants';
import { SIDE_NAV_DEFINITION } from '@react/components/SideNav/constants';
import { HOME_PLUGIN_SECTION_DEFINITION } from '@react/components/HomePluginSection/constants';
import { LOADING_SPINNER_DEFINITION } from '@react/components/Spinner/constants';
import { HOME_PLUGIN_CARD_ITEM_DEFINITION } from '@react/components/HomePluginCard';
import { ACCORDION_DEFINITION } from '@react/components/Accordion/constants';
import { TABLE_DEFINITION } from '@react/components/Table/constants';
import { CARD_TILE_DEFINITION } from '@react/components/CardTile/constants';
import { CARD_GRID_DEFINITION } from '@react/components/CardGrid/constants';
import { OIP_CARD_DEFINITION } from '@react/components/Card/constants';
import { OIP_BADGE_DEFINITION } from '@react/components/Badge/constants';

/**
 * Web component registry
 * Maps tag names to their definitions
 *
 * This is the single source of truth for all web components.
 *
 * To add a new web component:
 * 1. Create a COMPONENT_DEFINITION in the component's constants.ts
 * 2. Import the definition and tag name at the top of this file
 * 3. Add to WEB_COMPONENT_REGISTRY
 */
export const WEB_COMPONENT_REGISTRY = {
  [ACTION_LIST_DEFINITION.tagName]: ACTION_LIST_DEFINITION,
  [SIDE_NAV_DEFINITION.tagName]: SIDE_NAV_DEFINITION,
  [KVK_BRANCH_SELECTOR_DEFINITION.tagName]: KVK_BRANCH_SELECTOR_DEFINITION,
  [MATERIAL_ICON_DEFINITION.tagName]: MATERIAL_ICON_DEFINITION,
  [HOME_PLUGIN_SECTION_DEFINITION.tagName]: HOME_PLUGIN_SECTION_DEFINITION,
  [LOADING_SPINNER_DEFINITION.tagName]: LOADING_SPINNER_DEFINITION,
  [HOME_PLUGIN_CARD_ITEM_DEFINITION.tagName]: HOME_PLUGIN_CARD_ITEM_DEFINITION,
  [ACCORDION_DEFINITION.tagName]: ACCORDION_DEFINITION,
  [TABLE_DEFINITION.tagName]: TABLE_DEFINITION,
  [CARD_TILE_DEFINITION.tagName]: CARD_TILE_DEFINITION,
  [CARD_GRID_DEFINITION.tagName]: CARD_GRID_DEFINITION,
  [OIP_CARD_DEFINITION.tagName]: OIP_CARD_DEFINITION,
  [OIP_BADGE_DEFINITION.tagName]: OIP_BADGE_DEFINITION,
} as const;
