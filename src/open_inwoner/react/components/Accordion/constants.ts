import { WebComponentDefinition } from '@react/lib/web-component';
import type { IAccordionProps } from './Accordion';

export const ACCORDION_DEFINITION: WebComponentDefinition<
  'oip-accordion',
  IAccordionProps
> = {
  tagName: 'oip-accordion',
  propNames: ['title', 'subtitle', 'icon', 'children', 'initialOpen'],
  options: { shadow: false },
  importer: () => import('./Accordion'),
};
