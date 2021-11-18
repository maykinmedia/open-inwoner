import React from 'react';
import './H4.scss';
import {iHeadingProps} from './iHeadingProps';


/**
 * h4 element.
 */
export const H4 = (props: iHeadingProps) => {
  const { children, className, ..._props } = props;

  const getClassnames = () => {
    return `h4 ${className}`
  }

  return (
    <h4 className={ getClassnames() } { ..._props }>{children}</h4>
  );
}
