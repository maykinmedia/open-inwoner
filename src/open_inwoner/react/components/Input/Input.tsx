import clsx from 'clsx';
import { AnyComponent as AC, InputHTMLAttributes } from 'preact';
import {
  FormField,
  FormFieldDescription,
  FormFieldErrorMessage,
  FormLabel,
  Textbox,
} from '@utrecht/component-library-react/dist';
import './Input.scss';

export type InputProps = {
  label: string;
  name: string;
  required?: boolean;
  noLabel?: boolean;
  helpText?: string;
  errors?: string[];
  extraClasses?: string;
} & InputHTMLAttributes;

const Input: AC<InputProps> = ({
  label,
  name,
  required = true,
  noLabel,
  helpText,
  errors,
  extraClasses,
  className,
  ...props
}) => {
  const invalid = !!errors?.length;
  const descriptionId = helpText ? `${name}-description` : undefined;
  const errorId = invalid ? `${name}-error` : undefined;
  const ariaDescribedBy =
    [descriptionId, errorId].filter(Boolean).join(' ') || undefined;

  return (
    <FormField
      className={clsx(extraClasses, className)}
      invalid={invalid}
      label={
        <FormLabel htmlFor={name} className={noLabel ? 'sr-only' : undefined}>
          {label}
          {required && <span aria-hidden="true"> *</span>}
        </FormLabel>
      }
      description={
        helpText && (
          <FormFieldDescription id={descriptionId}>
            <nl-paragraph>{helpText}</nl-paragraph>
          </FormFieldDescription>
        )
      }
      input={
        <Textbox
          {...(props as any)}
          id={name}
          name={name}
          inputRequired={required}
          invalid={invalid}
          aria-describedby={ariaDescribedBy}
        />
      }
      errorMessage={
        invalid &&
        errors!.map((error, i) => (
          <FormFieldErrorMessage
            id={i === 0 ? errorId : undefined}
            key={i}
            role="alert"
          >
            {error}
          </FormFieldErrorMessage>
        ))
      }
    ></FormField>
  );
};

export default Input;
