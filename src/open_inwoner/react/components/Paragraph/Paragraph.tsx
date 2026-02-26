import { Paragraph as NLDSParagraph } from '@nl-design-system-candidate/paragraph-react';
import { AnyComponent as AC } from 'preact';

export interface IParagraphProps {
  lead?: boolean;
  extraClasses?: string; // To add more OIP modifiers
}

const Paragraph: AC<IParagraphProps> = ({
  children,
  lead = false,
  extraClasses,
}) => {
  return (
    <NLDSParagraph purpose={lead ? 'lead' : undefined} className={extraClasses}>
      {children}
    </NLDSParagraph>
  );
};

export default Paragraph;
