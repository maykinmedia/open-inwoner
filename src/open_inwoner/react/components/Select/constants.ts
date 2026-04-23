import { createStyleSheets } from '@react/lib/css';
import { WebComponentDefinition } from '@react/lib/web-component';
import selectStyle from './Select.scss?inline';
import selectOptionStyle from './SelectOption.scss?inline';
import { SelectProps } from './Select';
import { OptionProps } from './SelectOption';

export const SELECT_DEFINITION: WebComponentDefinition<
  'oip-select',
  SelectProps
> = {
  tagName: 'oip-select',
  propNames: ['name', 'label', 'value', 'alwaysOpen', 'multiple'],
  options: {
    shadow: true,
    formAssociated: true,
    adoptedStyleSheets: createStyleSheets(selectStyle),
    internals: { role: 'listbox' },
  },
  subComponents: ['oip-select-option'],
  importer: () => import('./Select'),
};

export const SELECT_OPTION_DEFINITION: WebComponentDefinition<
  'oip-select-option',
  OptionProps
> = {
  tagName: 'oip-select-option',
  propNames: ['value', 'label'],
  options: {
    shadow: true,
    adoptedStyleSheets: createStyleSheets(selectOptionStyle),
    internals: { role: 'option' },
  },
  importer: () => import('./SelectOption'),
};
