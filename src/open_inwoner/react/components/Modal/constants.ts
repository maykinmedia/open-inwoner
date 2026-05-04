import { createStyleSheets } from '@react/lib/css';
import { WebComponentDefinition } from '@react/lib/web-component';
import modalStyle from './Modal.scss?inline';
import buttonStyle from '../Button/Button.scss?inline';
import globalButtonStyle from '../../../scss/components/Button/Button.scss?inline';
export const MODAL_DEFINITION: WebComponentDefinition<'oip-modal'> = {
  tagName: 'oip-modal',
  propNames: [],
  options: {
    shadow: true,
    adoptedStyleSheets: createStyleSheets(modalStyle),
  },
  subComponents: [
    'oip-filter-modal',
    'oip-filter-modal-opener',
    'oip-modal-opener',
  ],
  importer: () => import('./Modal'),
};

export const MODAL_OPENER_DEFINITION: WebComponentDefinition<'oip-modal-opener'> =
  {
    tagName: 'oip-modal-opener',
    propNames: [],
    options: {
      shadow: true,
      i18n: false,
      adoptedStyleSheets: createStyleSheets(buttonStyle, globalButtonStyle),
      // adoptedStyleSheets: createStyleSheets(filterModalStyle),
    },
    importer: () => import('./ModalOpener'),
  };
