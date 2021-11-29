import React, {ReactElement} from 'react';
import './ProgressIndicator.scss';
import {iLinkProps, Link} from '../Typography/Link';


interface iProgressIndicatorProps {
  steps: iLinkProps[],
}


/**
 * Returns a progress indicator based.
 * @param {iProgressIndicatorProps} props
 * @return {ReactElement}
 */
export function ProgressIndicator(props: iProgressIndicatorProps): ReactElement {
  const {steps, ..._props} = props

  /**
   * Renders the steps.
   */
  const renderSteps = () => steps.map((step: iLinkProps, index: number): ReactElement => {
    let className = 'progress-indicator__list-item';
    if (step.active) {
      className += ` ${className}--active`
    }

    return (
      <li key={index} className={className} data-step={index + 1}>
        <Link {...step}/>
      </li>
    );
  });

  return (
    <aside className="progress-indicator" {..._props}>
      <ul className="progress-indicator__list">
        {renderSteps()}
      </ul>
    </aside>
  );
}
