import { ACTION_LIST_DEFINITION } from '@react/components/ActionList/constants';
import { KVK_BRANCH_SELECTOR_DEFINITION } from '@react/components/KVKBranchSelector/constants';
import { MATERIAL_ICON_DEFINITION } from '@react/components/MaterialIcon/constants';
import { SIDE_NAV_DEFINITION } from '@react/components/SideNav/constants';
import { HOME_PLUGIN_SECTION_DEFINITION } from '@react/components/HomePluginSection/constants';
import { LOADING_SPINNER_DEFINITION } from '@react/components/Spinner/constants';
import { HOME_PLUGIN_CARD_ITEM_DEFINITION } from '@react/components/HomePluginCard';
import { ACCORDION_DEFINITION } from '@react/components/Accordion/constants';
import { CHART_DEFINITION } from '@react/components/Chart/constants';
import {
  TABLE_CONTAINER_DEFINITION,
  TABLE_DEFINITION,
  TABLE_CAPTION_DEFINITION,
  TABLE_HEADER_DEFINITION,
  TABLE_HEADER_CELL_DEFINITION,
  TABLE_BODY_DEFINITION,
  TABLE_ROW_DEFINITION,
  TABLE_CELL_DEFINITION,
  TABLE_FOOTER_DEFINITION,
} from '@react/components/Table/constants';

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
  [CHART_DEFINITION.tagName]: CHART_DEFINITION,
  [TABLE_CONTAINER_DEFINITION.tagName]: TABLE_CONTAINER_DEFINITION,
  [TABLE_CAPTION_DEFINITION.tagName]: TABLE_CAPTION_DEFINITION,
  [TABLE_HEADER_DEFINITION.tagName]: TABLE_HEADER_DEFINITION,
  [TABLE_HEADER_CELL_DEFINITION.tagName]: TABLE_HEADER_CELL_DEFINITION,
  [TABLE_BODY_DEFINITION.tagName]: TABLE_BODY_DEFINITION,
  [TABLE_ROW_DEFINITION.tagName]: TABLE_ROW_DEFINITION,
  [TABLE_CELL_DEFINITION.tagName]: TABLE_CELL_DEFINITION,
  [TABLE_FOOTER_DEFINITION.tagName]: TABLE_FOOTER_DEFINITION,
} as const;
