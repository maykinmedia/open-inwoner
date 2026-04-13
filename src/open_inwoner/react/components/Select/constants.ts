import { createStyleSheets } from '@react/lib/css';
import { WebComponentDefinition } from '@react/lib/web-component';
import selectStyle from './Select.scss?inline';
import selectOptionStyle from './SelectOption.scss?inline';
import { SelectProps } from './Select';
import { OptionProps } from './SelectOption';

export const SELECT_DEFINITION: WebComponentDefinition<
  'oip-sig-list-test',
  SelectProps
> = {
  tagName: 'oip-sig-list-test',
  propNames: ['name', 'label', 'alwaysOpen', 'multiple'],
  options: {
    shadow: true,
    adoptedStyleSheets: createStyleSheets(selectStyle),
  },
  importer: () => import('./Select'),
};
export const SELECT_OPTION_DEFINITION: WebComponentDefinition<
  'oip-sig-option-test',
  OptionProps
> = {
  tagName: 'oip-sig-option-test',
  propNames: ['group', 'value', 'label', 'checkbox', 'initialSelected'],
  options: {
    shadow: true,
    adoptedStyleSheets: createStyleSheets(selectOptionStyle),
  },
  importer: () => import('./SelectOption'),
};
