import { WebComponentDefinition } from '@react/lib/web-component';
import { createStyleSheets } from '@react/lib/css';
import type { IAccordionProps } from './Accordion';
import style from './Accordion.scss?inline';

export const ACCORDION_DEFINITION: WebComponentDefinition<
  'oip-accordion',
  IAccordionProps
> = {
  tagName: 'oip-accordion',
  propNames: ['initialOpen'],
  options: { shadow: true, adoptedStyleSheets: createStyleSheets(style) },
  importer: () => import('./Accordion'),
};
