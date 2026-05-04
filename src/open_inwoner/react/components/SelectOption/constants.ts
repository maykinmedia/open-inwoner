import { WebComponentDefinition } from '@react/lib/web-component';
import { OptionProps } from '../SelectOption/SelectOption';
import { createStyleSheets } from '@react/lib/css';
import selectOptionStyle from './SelectOption.scss?inline';

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
  importer: () => import('../SelectOption/SelectOption'),
};
