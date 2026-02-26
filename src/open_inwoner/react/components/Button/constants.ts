import { WebComponentDefinition } from '@react/lib/web-component';
import type { ButtonProps } from './Button';

export const BUTTON_DEFINITION: WebComponentDefinition<
  'oip-button',
  ButtonProps
> = {
  tagName: 'oip-button',
  propNames: [],
  options: { shadow: false },
  importer: () => import('./Button'),
};
