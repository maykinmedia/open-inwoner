/**
 * KVK Branch Selector constants
 *
 * This is the single source of truth for the KVKBranchSelector component.
 * The central registry built from these definitions.
 */
import { WebComponentDefinition } from '@react/lib/web-component';
import type { KVKBranchSelectorProps } from './KVKBranchSelector';

export const WEB_COMPONENT_NAME = 'kvk-branch-selector' as const;

export const KVK_BRANCH_SELECTOR_DEFINITION: WebComponentDefinition<KVKBranchSelectorProps> =
  {
    tagName: WEB_COMPONENT_NAME,
    propNames: [
      'id',
      'label',
      'name',
      'branches',
      'selectedBranchId',
      'branchesId',
    ],
    options: { shadow: false, i18n: true },
    importer: () => import('./KVKBranchSelector'),
  };
