import React, {ReactElement} from 'react';
import './CardContainer.scss';

interface iCardContainerProps {
  small?: boolean,
  children?: any,
}

/**
 * A wrapper for cards.
 * @param {iCardContainerProps} props
 * @return {ReactElement}
 */
export function CardContainer(props: iCardContainerProps): ReactElement {
  const getClassNames = () => {
    let classnames = "card-container"
    if (props.small) {
      classnames += " card-container--small"
    }
    return classnames
  }

  return (
    <div className={ getClassNames() }>
      {props.children}
    </div>
  );
}
