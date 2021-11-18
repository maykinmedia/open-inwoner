import React, { ReactElement } from 'react';
import './Divider.scss';

interface DividerProps {
  small?: boolean,
}

export function Divider(props: DividerProps): ReactElement {
  const { small } = props

  const getClassNames = () => {
    let classnames = "divider"
    if (small) {
      classnames += " divider--small"
    }
    return classnames;
  }

  return (
    <hr className={ getClassNames() } />
  );
}
