import React from 'react';
import './Submit.scss';

interface SubmitProps {
    value: string,
    name: string,
}

export function Submit(props:SubmitProps) {
  return (
    <input
      className="submit"
      type="submit"
      value={props.value}
      name={props.name}
      id={`id_${props.name}`}
    />
  );
}
