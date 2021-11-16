import React from 'react';
import './H4.scss';
import {iHeadingProps} from './iHeadingProps';


/**
 * h4 element.
 */
export const H4 = (props: iHeadingProps) => {
  return (
    <h4 className="h4">{props.children}</h4>
  );
}
