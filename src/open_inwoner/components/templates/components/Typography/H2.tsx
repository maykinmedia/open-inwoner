import React from 'react';
import {iHeadingProps} from './iHeadingProps';
import './H2.scss';


/**
 * h3 element.
 */
export const H2 = (props: iHeadingProps) => {
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
    <h2 className="h2" id={getId()} {..._props}>{children}</h2>
  );
}
