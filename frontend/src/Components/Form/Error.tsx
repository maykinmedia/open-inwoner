import React, {ReactElement} from 'react';
import './Error.scss';


interface iErrorProps {
  children: any,
}

/**
 * Shows an error.
 * @param {iErrorProps} props
 * @return {ReactElement}
 */
export function Error(props: iErrorProps): ReactElement {
  return (
    <div className="error">{props.children}</div>
  );
}
