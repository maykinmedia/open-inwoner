import { WebComponentDefinition } from '@react/lib/web-component';
import { ListProps } from './Mid';
import { RootProps } from './Root';

export const SIG_ROOT_DEFINITION: WebComponentDefinition<
  'oip-sig-root',
  RootProps
> = {
  tagName: 'oip-sig-root',
  propNames: ['data', 'dataId'],
  options: { shadow: true },
  importer: () => import('./Root'),
  subComponents: ['oip-sig-list', 'oip-sig-summary'],
};

export const SIG_LIST_DEFINITION: WebComponentDefinition<
  'oip-sig-list',
  ListProps
> = {
  tagName: 'oip-sig-list',
  propNames: ['name', 'checkbox'],
  options: { shadow: true },
  importer: () => import('./Mid'),
};

export const SIG_SUMMARY_DEFINITION: WebComponentDefinition<'oip-sig-summary'> =
  {
    tagName: 'oip-sig-summary',
    propNames: [],
    options: { shadow: true },
    importer: () => import('./Leaf'),
  };
