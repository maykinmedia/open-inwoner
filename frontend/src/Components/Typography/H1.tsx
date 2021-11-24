import React from 'react';
import {iHeadingProps} from './iHeadingProps';
import './H1.scss';


/**
 * h1 element.
 */
export const H1 = (props: iHeadingProps) => {
  const {autoId, id, children, ..._props} = props;

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
    <h1 className="h1" id={getId()} {..._props}>{children}</h1>
  );
}
