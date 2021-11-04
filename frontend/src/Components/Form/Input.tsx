import React from 'react';
import './Input.scss';

interface InputProps {
    type: string,
    value?: string,
    name: string,
    required: boolean,
    changeAction: Function,
}

export function Input(props:InputProps) {
  const handleOnChange = (event: any) => {
    if (props.changeAction) {
      props.changeAction(event);
    }
  };

  return (
    <input
      className="input"
      type={props.type}
      value={props.value}
      name={props.name}
      id={`id_${props.name}`}
      required={props.required}
      onChange={handleOnChange}
    />
  );
}
