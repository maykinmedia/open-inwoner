import { WebComponentDefinition } from '@react/lib/web-component';
import { createStyleSheets } from '@react/lib/css';
import type { IParagraphProps } from './Paragraph';
import style from './Paragraph.scss?inline';

export const PARAGRAPH_DEFINITION: WebComponentDefinition<
  'nl-paragraph',
  IParagraphProps
> = {
  tagName: 'nl-paragraph',
  propNames: ['purpose', 'className'],
  options: { shadow: true, adoptedStyleSheets: createStyleSheets(style) },
  importer: () => import('./Paragraph'),
};
