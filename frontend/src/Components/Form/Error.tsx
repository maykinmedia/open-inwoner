import React from 'react';
import './Error.scss';

export function Error(props:any) {
  return (
    <div className="error">{ props.children }</div>
  );
}
