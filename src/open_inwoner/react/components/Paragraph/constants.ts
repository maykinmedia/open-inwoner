import { WebComponentDefinition } from '@react/lib/web-component';
import type { IParagraphProps } from './Paragraph';

export const PARAGRAPH_DEFINITION: WebComponentDefinition<
  'nl-paragraph',
  IParagraphProps
> = {
  tagName: 'nl-paragraph',
  propNames: ['lead', 'extraClasses'],
  options: { shadow: false },
  importer: () => import('./Paragraph'),
};
