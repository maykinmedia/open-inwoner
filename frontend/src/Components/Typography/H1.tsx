import React from 'react';
import './H1.scss';
import {iHeadingProps} from './iHeadingProps';


/**
 * h1 element.
 */
export const H1 = (props: iHeadingProps) => {
  const { children, className, ..._props } = props;

  const getClassnames = () => {
    return `h1 ${className}`
  }

  return (
    <h1 className={getClassnames()} { ..._props }>{children}</h1>
  );
}
