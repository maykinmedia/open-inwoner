import { createStyleSheets } from '@react/lib/css';
import { WebComponentDefinition } from '@react/lib/web-component';
import fieldsetStyle from './Fieldset.scss?inline';
import { FieldsetProps } from './Fieldset';

export const FIELDSET_DEFINITION: WebComponentDefinition<
  'oip-fieldset',
  FieldsetProps
> = {
  tagName: 'oip-fieldset',
  propNames: ['name', 'label', 'value', 'multiple'],
  options: {
    shadow: true,
    formAssociated: true,
    adoptedStyleSheets: createStyleSheets(fieldsetStyle),
    i18n: true,
  },
  subComponents: ['oip-fieldset-option'],
  importer: () => import('./Fieldset'),
};
