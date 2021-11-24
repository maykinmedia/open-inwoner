import React from 'react';
import {iHeadingProps} from './iHeadingProps';
import './H3.scss';


/**
 * h3 element.
 */
export const H3 = (props: iHeadingProps) => {
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
    <h3 className="h3" id={getId()} {..._props}>{children}</h3>
  );
}
