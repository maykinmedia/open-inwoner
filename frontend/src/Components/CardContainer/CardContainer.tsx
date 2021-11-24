import React, {ReactElement} from 'react';
import './CardContainer.scss';

interface iCardContainerProps {
  children?: any,
}

/**
 * A wrapper for cards.
 * @param {iCardContainerProps} props
 * @return {ReactElement}
 */
export function CardContainer(props: iCardContainerProps): ReactElement {
  return (
    <div className="card-container">
      {props.children}
    </div>
  );
}
