import React, {ReactElement, SyntheticEvent, useRef} from 'react';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import {iField} from '../../types/field';
import {Button, iButtonProps} from '../Button/Button';
import {Textarea} from './Textarea';
import {Select} from './Select';
import {Input} from './Input';
import {Label} from './Label';
import './Form.scss';
import {Error} from "./Error";


interface iFormProps {
  action?: string,
  actions?: iButtonProps[],
  children?: any,
  columns?: number,
  inline?: boolean,
  encType?: string
  errors?: string[],
  fields?: iField[],
  method?: string,
  submitLabel?: string,
  onSubmit?: Function,
  actionSize?: 'big' | 'normal' | undefined,
}


/**
 * Renders a form with fields.
 * @param {iFormProps} props
 * @return {ReactElement}
 */
export function Form(props: iFormProps): ReactElement {
  const {action, actionSize, actions, children, inline, columns, encType, errors, fields, method, submitLabel, onSubmit, ..._props} = props
  const formRef = useRef<HTMLFormElement>(null);

  /**
   * Handles the form submit.
   * @param event
   */
  const handleSubmit = (event: SyntheticEvent): void => {
    if (!onSubmit || !formRef.current) {
      return;
    }

    const data = serializeForm(formRef.current);
    onSubmit(event, data);
  }

  /**
   * Serializes form.
   * @param {HTMLFormElement} form
   * @return {Object}
   */
  const serializeForm = (form: HTMLFormElement): {[index: string]: any} => {
    const formData = new FormData(form);
    return [...formData].reduce((acc: { [index: string]: any }, [key, value]) => {
      if (!Reflect.has(acc, key)) {
        acc[key] = value;
        return acc;
      }

      if (!Array.isArray(acc[key])) {
        acc[key] = [acc[key]];
        return acc;
      }
      acc[key].push(value);
      return acc;
    }, {});
  }

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

  const getClassNames = () => {
    let classnames = `form form--columns-${columns}`
    if (inline) {
      classnames += " form--inline"
    }
    return classnames
  }

  return (
    <form ref={formRef} className={getClassNames()} action={action} encType={encType} method={method} onSubmit={handleSubmit} {..._props}>
      {children}

      {errors?.map((error) => <Error key={error}>{error}</Error>)}

      {renderFormControls()}

      <div className="form__actions">
        {actions?.map((action, index) => <Button key={index} {...action}/>)}
        <Button icon={ArrowForwardIcon} iconPosition="after" primary={true} size={actionSize} type="submit">{submitLabel}</Button>
      </div>
    </form>
  );
}

Form.defaultProps = {
  actions: [],
  columns: 1,
  fields: [],
  method: 'GET',
  submitLabel: 'Verzenden',
  actionSize: 'big'
}
