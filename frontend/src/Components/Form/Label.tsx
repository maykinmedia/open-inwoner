import React, {ReactElement} from 'react';
import './Label.scss';

interface iLabelProps {
  htmlFor?: string,
  children?: any
}

/**
 * Renders a label.
 * @param {iLabelProps} props
 * @return {ReactElement}
 */
export function Label(props: iLabelProps): ReactElement {
  const {children, htmlFor, ..._props} = props

  return (
    <label className="label" htmlFor={htmlFor} {..._props}>
      {children}
    </label>
  );
}
