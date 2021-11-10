import React, {ReactElement} from 'react';
import {iField} from '../../types/field';
import './Input.scss';


interface iInputProps {
  field: iField,
}

/**
 * Returns an input based on field.
 * @param {iInputProps} props
 * @return {ReactElement}
 */
export function Input(props: iInputProps): ReactElement {
  const {field, ..._props} = props;

  return (
    <input className="input" title={field.label} name={field.name} type={field.type}
           value={field.value} {...field.attrs} {..._props}/>
  )
}
