import React from 'react';
import './Container.scss';

export function Container(props:any) {
  return (
    <main className="container">{ props.children }</main>
  );
}
