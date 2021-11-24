import React, {ReactElement} from 'react';
import {iField} from '../../types/field';
import './Textarea.scss';
import {Error} from "./Error";


interface iTextareaProps {
  field: iField,
  children?: any
}

/**
 * Returns a textarea based on field.
 * @param {iTextareaProps} props
 * @return {ReactElement}
 */
export function Textarea(props: iTextareaProps): ReactElement {
  const {field, children, ..._props} = props;
  const required = (typeof field.required === 'undefined') ? true : field.required;

  return (
    <>
      <textarea className="textarea" title={field.label} name={field.name} required={required} {...field.attrs} {..._props}>
        {field.value || children}
      </textarea>
      {field.errors?.map((error) => <Error key={error}>{error}</Error>)}
    </>
  )
}
