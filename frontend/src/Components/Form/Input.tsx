import React, {ReactElement} from 'react';
import {iField} from '../../types/field';
import {Error} from './Error'
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
  const required = (typeof field.required === 'undefined') ? true : field.required;

  return (
    <>
      <input className="input" title={field.label} name={field.name} required={required} type={field.type}
             value={field.value} {...field.attrs} {..._props}/>
      {field.errors?.map((error) => <Error key={error}>{error}</Error>)}
    </>
  )
}
