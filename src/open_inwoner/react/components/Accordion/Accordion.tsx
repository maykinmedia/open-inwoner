import { AnyComponent as AC } from 'preact';
import './Accordion.scss';
import { normalizeBoolean } from '@react/lib/attributes/attribute';
import { BooleanLike } from '@react/types/attributes';

/**
 * Props for the Accordion web component.
 *
 * @prop initialOpen - Whether the accordion is open on initial render. Accepts boolean or boolean-like string (e.g. `"true"`). Defaults to `false`.
 */
export interface IAccordionProps {
  initialOpen?: BooleanLike;
}

/**
 * Accordion — a collapsible disclosure widget built on native `<details>`/`<summary>` elements.
 *
 * Designed as a web component (`<oip-accordion>`). Accepts content via named slots:
 * - `summary`: heading/title area
 * - `icon`: toggle icon (e.g. `<material-icon>`)
 * - default slot: disclosed content
 */
const Accordion: AC<IAccordionProps> = ({ initialOpen = 'false' }) => {
  const normalizedInitialOpen = normalizeBoolean(initialOpen);

  return (
    <details class="accordion" open={normalizedInitialOpen}>
      <summary class="accordion__summary">
        <slot name="summary" />
        <slot name="icon" class="accordion__icon" />
      </summary>
      <slot />
    </details>
  );
};

export default Accordion;
