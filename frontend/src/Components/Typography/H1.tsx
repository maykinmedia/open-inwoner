import React from 'react';
import './H1.scss';
import {iHeadingProps} from './iHeadingProps';


/**
 * h1 element.
 */
export const H1 = (props: iHeadingProps) => {
  return (
    <h1 className="h1">{props.children}</h1>
  );
}
