import React from 'react';
import {iHeadingProps} from './iHeadingProps';
import './H4.scss';


/**
 * h4 element.
 */
export const H4 = (props: iHeadingProps) => {
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
    <h4 className="h4" id={getId()} {..._props}>{children}</h4>
  );
}
