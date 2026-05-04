import { WebComponentDefinition } from '@react/lib/web-component';
import type { ButtonProps } from './Button';
import filterButtonStyling from './Button.scss?inline';
import filterButtonStyling2 from '../../../scss/components/Button/Button.scss?inline';
import { createStyleSheets } from '@react/lib/css';

export const BUTTON_DEFINITION: WebComponentDefinition<
  'oip-button',
  ButtonProps
> = {
  tagName: 'oip-button',
  propNames: [],
  options: {
    shadow: true,
    adoptedStyleSheets: createStyleSheets(
      filterButtonStyling,
      filterButtonStyling2
    ),
  },
  importer: () => import('./Button'),
};
