import React from 'react';
import {iHeadingProps} from './iHeadingProps';
import './H4.scss';


/**
 * h4 element.
 */
export const H4 = (props: iHeadingProps) => {
  const {autoId, id, className, children, ..._props} = props;

  const getClassnames = () => {
    return `h4 ${className}`
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
    <h4 className={ getClassnames() } id={getId()} {..._props}>{children}</h4>
  );
}
