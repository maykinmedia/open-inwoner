import React, {ReactElement} from 'react';
import {iField} from '../../types/field';
import { Error } from './Error'
import { Label } from './Label'
import './Checkbox.scss';


interface iCheckboxProps {
  field: iField,
  onChange: Function,
}

/**
 * Returns an input based on field.
 * @param {iCheckboxProps} props
 * @return {ReactElement}
 */
export function Checkbox(props: iCheckboxProps): ReactElement {
  const {field, onChange, ..._props} = props;
  const required = (typeof field.required === 'undefined') ? true : field.required;
  const checked = (typeof field.selected === 'undefined') ? false : field.selected;

  const stopPropagation = (event) => {
    event.stopPropagation();
  }

  return (
    <label className="checkbox" onClick={ stopPropagation }>
      <input onChange={onChange} id={ field.id } className="checkbox__input" title={field.label} name={field.name} required={required} type='checkbox'
        defaultChecked={checked} value={field.value} {...field.attrs} {..._props}/>
      <Label className="checkbox__label" htmlFor={ field.id }>{ field.label }</Label>
      {field.errors?.map((error) => <Error key={error}>{error}</Error>)}
    </label>
  )
}
