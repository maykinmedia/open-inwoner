import { createStyleSheets } from '@react/lib/css';
import { WebComponentDefinition } from '@react/lib/web-component';
import fieldsetOptionStyle from './FieldsetOption.scss?inline';
import { FieldsetOptionProps } from './FieldsetOption';

export const FIELDSET_OPTION_DEFINITION: WebComponentDefinition<
  'oip-fieldset-option',
  FieldsetOptionProps
> = {
  tagName: 'oip-fieldset-option',
  propNames: ['value', 'label'],
  options: {
    shadow: true,
    adoptedStyleSheets: createStyleSheets(fieldsetOptionStyle),
  },
  importer: () => import('./FieldsetOption'),
};
