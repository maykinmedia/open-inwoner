import React from 'react';
import './P.scss';

interface iBodyProps {
  autoId?: boolean,
  id?: string,
  children?: any,
}

/**
 * p element.
 */
export const P = (props: iBodyProps) => {
  const {autoId, id, children, ..._props} = props;

  /**
   * Returns the id.
   */
  const getId = (): string | undefined => {
    if (autoId) {
      return String(children).replace(/\s+/g, '-').toLowerCase();
    }
    return id;
  }

  return (
    <p className="p" id={getId()} {..._props}>{props.children}</p>
  );
}
