import React, {ReactElement} from 'react';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import {iField} from '../../types/field';
import {Button} from '../Button/Button';
import {Textarea} from './Textarea';
import {Select} from './Select';
import {Input} from './Input';
import {Label} from './Label';
import './Form.scss';

interface iFormProps {
  action?: string,
  children?: any,
  columns: number,
  encType?: string
  fields?: iField[],
  method?: string,
  submitLabel?: string,
}


/**
 * Renders a form with fields.
 * @param {iFormProps} props
 * @return {ReactElement}
 */
export function Form(props: iFormProps): ReactElement {
  const {action, children, columns, encType, fields, method, submitLabel, ..._props} = props

  /**
   * Renders form controls.
   */
  const renderFormControls = (): ReactElement[] => (
    fields?.map(renderFormControl) || []
  );

  /**
   * Renders a form control.
   * @param {iField} field
   * @param {*} [key]
   */
  const renderFormControl = (field: iField, key: any = null): ReactElement => (
    <div className="form__control">
      <Label>
        {field.label && field.label}
        {renderField(field, key)}
      </Label>
    </div>
  )

  /**
   * Renders a field.
   * @param {iField} field
   * @param {*} [key]
   */
  const renderField = (field: iField, key: any = null): ReactElement => {
    const {name, type, attrs, value} = field;
    if (type === 'button') {
      return (
        <Button key={key} name={name} value={value} {...attrs}>{field.label}</Button>
      );
    }

    if (type === 'select') {
      return (
        <Select key={key} field={field}/>
      );
    }

    if (type === 'textarea') {
      return (
        <Textarea key={key} field={field}/>
      );
    }

    return <Input key={key} field={field}/>
  }

  return (
    <form className={`form form--columns-${columns}`} action={action} encType={encType} method={method} {..._props}>
      {children}
      {renderFormControls()}

      <div className="form__actions">
        <Button size="big" type="submit">{submitLabel}<ArrowForwardIcon/></Button>
      </div>
    </form>
  );
}

Form.defaultProps = {
  columns: 1,
  fields: [],
  method: 'GET',
  submitLabel: 'Verzenden',
}
