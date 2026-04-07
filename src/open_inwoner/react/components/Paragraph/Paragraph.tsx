import {
  Paragraph as NLDSParagraph,
  type ParagraphProps,
} from '@nl-design-system-candidate/paragraph-react';
import { AnyComponent as AC } from 'preact';
import './Paragraph.scss';

export type IParagraphProps = ParagraphProps;

const Paragraph: AC<IParagraphProps> = ({ children, ...props }) => {
  return <NLDSParagraph {...props}>{children}</NLDSParagraph>;
};

export default Paragraph;
