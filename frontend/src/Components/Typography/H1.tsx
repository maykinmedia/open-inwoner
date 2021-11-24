import React from 'react';
import {iHeadingProps} from './iHeadingProps';
import './H1.scss';


/**
 * h1 element.
 */
export const H1 = (props: iHeadingProps) => {
  const {autoId, id, className, children, ..._props} = props;

  const getClassnames = () => {
    return `h1 ${className}`
  }

  /**
   * Returns the id.
   */
  const getId = (): string | undefined => {
    if(autoId) {
      return String(children).replace(/\s+/g, '-').toLowerCase();
    }
    return id;
  }

  return (
    <h1 className={getClassnames()} id={getId()} {..._props}>{children}</h1>
  );
}
