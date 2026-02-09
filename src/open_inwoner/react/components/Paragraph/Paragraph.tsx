import { Paragraph as NLDSParagraph } from '@nl-design-system-candidate/paragraph-react';
import { AnyComponent as AC } from 'preact';

export interface IParagraphProps {
  lead?: boolean;
}

const Paragraph: AC<IParagraphProps> = ({ children, lead = false }) => {
  return (
    <NLDSParagraph purpose={lead ? 'lead' : undefined}>
      {children}
    </NLDSParagraph>
  );
};

export default Paragraph;
