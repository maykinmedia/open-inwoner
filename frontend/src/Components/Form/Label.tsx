import React, {ReactElement} from 'react';
import './Label.scss';

interface iLabelProps {
  htmlFor?: string,
  children?: any,
  className?: string,
}

/**
 * Renders a label.
 * @param {iLabelProps} props
 * @return {ReactElement}
 */
export function Label(props: iLabelProps): ReactElement {
  const { children, htmlFor, className, ..._props } = props

  const getClassNames = () => {
    return `label ${className}`
  }

  return (
    <label className={ getClassNames() } htmlFor={htmlFor} {..._props}>
      {children}
    </label>
  );
}
