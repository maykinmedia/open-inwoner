import { AnyComponent as AC, ComponentChildren } from 'preact';
import { MaterialIcon } from '../MaterialIcon';
import './Accordion.scss';
import { normalizeBoolean } from '@react/lib/attributes/attribute';
import { BooleanLike } from '@react/types/attributes';

export interface IAccordionProps {
  title?: string;
  subtitle?: string;
  icon?: string;
  initialOpen?: BooleanLike;
  children?: ComponentChildren;
}

const Accordion: AC<IAccordionProps> = ({
  title,
  subtitle,
  icon = 'keyboard_arrow_down',
  initialOpen = 'false',
  children,
}) => {
  const HeadingElement = title && subtitle ? 'h2' : 'p';
  const normalizedInitialOpen = normalizeBoolean(initialOpen);

  return (
    <details className="accordion" open={normalizedInitialOpen}>
      <summary className="accordion__summary">
        <div className="accordion__heading">
          {title && (
            <HeadingElement className="utrecht-heading-3">
              {title}
            </HeadingElement>
          )}
          {subtitle && <p className="utrecht-paragraph">{subtitle}</p>}
        </div>
        <MaterialIcon name={icon} extraClassName={['accordion__icon']} />
      </summary>
      {children}
    </details>
  );
};

export default Accordion;
