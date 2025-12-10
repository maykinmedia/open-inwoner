import { WebComponentDefinition } from '@react/lib/web-component';
import type { KVKBranchSelectorProps } from './KVKBranchSelector';

export const KVK_BRANCH_SELECTOR_DEFINITION: WebComponentDefinition<
  'kvk-branch-selector',
  KVKBranchSelectorProps
> = {
  tagName: 'kvk-branch-selector',
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
