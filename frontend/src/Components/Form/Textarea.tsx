import React, {ReactElement} from 'react';
import {iField} from '../../types/field';
import './Textarea.scss';


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

  return (
    <textarea className="textarea" title={field.label} name={field.name} {...field.attrs} {..._props}>
      {field.value || children}
    </textarea>
  )
}
