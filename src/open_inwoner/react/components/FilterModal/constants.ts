import { createStyleSheets } from '@react/lib/css';
import { WebComponentDefinition } from '@react/lib/web-component';
import filterModalStyle from './FilterModal.scss?inline';

export const FILTER_MODAL_DEFINITION: WebComponentDefinition<'oip-filter-modal'> =
  {
    tagName: 'oip-filter-modal',
    propNames: [],
    options: {
      shadow: true,
      i18n: true,
      adoptedStyleSheets: createStyleSheets(filterModalStyle),
    },
    subComponents: ['oip-filter-modal-opener'],
    importer: () => import('./FilterModal'),
  };

export const FILTER_MODAL_OPENER_DEFINITION: WebComponentDefinition<'oip-filter-modal-opener'> =
  {
    tagName: 'oip-filter-modal-opener',
    propNames: [],
    options: {
      shadow: true,
      i18n: true,
      adoptedStyleSheets: createStyleSheets(filterModalStyle),
    },
    importer: () => import('./FilterModalOpener'),
  };
