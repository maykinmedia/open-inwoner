import React, { ReactElement} from 'react';

import './ButtonRow.scss'

interface iButtonRowProps {
  startingText: string,
  buttons: Array<ReactElement>,
}

export function ButtonRow(props: iButtonRowProps) {
  return (
    <div className="button-row">
      { props.startingText }
      { props.buttons }
    </div>
  );
}
