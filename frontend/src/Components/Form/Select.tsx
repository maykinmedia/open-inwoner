import React, {ReactElement} from 'react';
import {iField} from '../../types/field';
import {iChoice} from '../../types/choice';
import './Select.scss';

interface iSelectProps {
  field: iField,
}

/**
 * Returns a select based on field.
 * @param {iSelectProps} props
 * @return {ReactElement}
 */
export function Select(props: iSelectProps): ReactElement {
  const {field, ..._props} = props;

  /**
   * Renders the options.
   * @return {ReactElement[]}
   */
  const renderOptions = (): ReactElement[] => {
    return field.choices?.map((choice: iChoice) => (
      <option key={choice.value} value={choice.value} selected={field.value === choice.value}>{choice.label}</option>
    )) || [];
  };

  return (
    <select className="select" title={field.label} name={field.name} {...field.attrs} {..._props}>
      {renderOptions()}
    </select>
  )
}
