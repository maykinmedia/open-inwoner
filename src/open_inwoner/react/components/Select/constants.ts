import { createStyleSheets } from '@react/lib/css';
import { WebComponentDefinition } from '@react/lib/web-component';
import selectStyle from './Select.scss?inline';
import { SelectProps } from './Select';

export const SELECT_DEFINITION: WebComponentDefinition<
  'oip-select',
  SelectProps
> = {
  tagName: 'oip-select',
  propNames: ['name', 'label', 'value', 'multiple'],
  options: {
    shadow: true,
    formAssociated: true,
    adoptedStyleSheets: createStyleSheets(selectStyle),
    internals: { role: 'listbox' },
    i18n: true,
  },
  subComponents: ['oip-select-option', 'material-icon'],
  importer: () => import('./Select'),
};
