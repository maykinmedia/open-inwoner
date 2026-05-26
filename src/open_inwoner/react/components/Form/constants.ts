import { createStyleSheets } from '@react/lib/css';
import { WebComponentDefinition } from '@react/lib/web-component';
import buttonStyle from '../Button/Button.scss?inline';
import globalButtonStyle from '../../../scss/components/Button/Button.scss?inline';

export const FORM_COMPONENT_DEFINITION: WebComponentDefinition<'oip-form'> = {
  tagName: 'oip-form',
  propNames: [],
  options: {
    shadow: true,
    i18n: true,
  },
  subComponents: [
    'oip-filters',
    'oip-form-button',
    'oip-form-reset-button',
    'oip-select',
    'oip-fieldset',
    'oip-modal',
  ],
  importer: () => import('./Form'),
};

export const FORM_BUTTON_DEFINITION: WebComponentDefinition<'oip-form-button'> =
  {
    tagName: 'oip-form-button',
    propNames: [],
    options: {
      shadow: true,
      i18n: true,
      // Both the component-scoped and global design-system button styles are
      // required so the Button component renders correctly inside shadow DOM.
      adoptedStyleSheets: createStyleSheets(buttonStyle, globalButtonStyle),
    },
    importer: () => import('./components/FormButton'),
  };
export const FORM_RESET_BUTTON_DEFINITION: WebComponentDefinition<'oip-form-reset-button'> =
  {
    tagName: 'oip-form-reset-button',
    propNames: [],
    options: {
      shadow: true,
      i18n: true,
      // Both the component-scoped and global design-system button styles are
      // required so the Button component renders correctly inside shadow DOM.
      adoptedStyleSheets: createStyleSheets(buttonStyle, globalButtonStyle),
    },
    importer: () => import('./components/FormResetButton'),
  };
