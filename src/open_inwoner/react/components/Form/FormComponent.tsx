import { computed, useSignal } from '@preact/signals';
import isEqual from 'lodash/isEqual';
import mapValues from 'lodash/mapValues';
import xor from 'lodash/xor';
import { type AnyComponent as AC } from 'preact';
import { useRef } from 'preact/hooks';
import { FormContext, type FormFieldBinding } from './FormContext';

/**
 * oip-form
 * Root context provider for form-bound select components.
 * Manages field values and initial state; knows field names and current values
 * but does not enumerate individual options (those register their own labels).
 */
const FormComponent: AC<{}> = ({ children }) => {
  const values = useSignal<Record<string, string[]>>({});
  const initial = useRef<Record<string, string[]>>({});
  const optionLabels = useRef<Record<string, Record<string, string>>>({});
  const bindings = useRef<Record<string, FormFieldBinding>>({});

  const isDirty = computed(() => !isEqual(values.value, initial.current));
  const isEmpty = computed(() =>
    Object.values(values.value).every((v) => v.length === 0)
  );

  const register = (
    name: string,
    defaultValue?: string[]
  ): FormFieldBinding => {
    if (!bindings.current[name]) {
      const def = defaultValue ?? [];
      values.value = { ...values.value, [name]: def };
      initial.current[name] = def;
      bindings.current[name] = {
        value: computed(() => values.value[name] ?? []),
        setValue: (v: string[]) => {
          values.value = { ...values.value, [name]: v };
        },
      };
    }
    return bindings.current[name];
  };

  const registerLabel = (
    fieldName: string,
    value: string,
    label: string
  ): void => {
    if (!optionLabels.current[fieldName]) {
      optionLabels.current[fieldName] = {};
    }
    optionLabels.current[fieldName][value] = label;
  };

  const getLabel = (fieldName: string, value: string): string =>
    optionLabels.current[fieldName]?.[value] ?? value;

  const removeValue = (fieldName: string, value: string): void => {
    const current = values.value[fieldName] ?? [];
    values.value = {
      ...values.value,
      [fieldName]: current.filter((v) => v !== value),
    };
  };

  const toggle = (
    fieldName: string,
    value: string,
    multiple: boolean
  ): void => {
    const current = values.value[fieldName] ?? [];
    const next = multiple ? xor(current, [value]) : [value];
    values.value = { ...values.value, [fieldName]: next };
  };

  const reset = (): void => {
    values.value = mapValues(values.value, () => []);
  };

  const submit = (): void => {
    const params = new URLSearchParams();
    Object.entries(values.value).forEach(([key, vals]) => {
      vals.forEach((v) => params.append(key, v));
    });
    window.location.href = `${window.location.pathname}?${params}`;
  };

  return (
    <FormContext.Provider
      value={{
        register,
        registerLabel,
        getLabel,
        values,
        removeValue,
        toggle,
        isDirty,
        isEmpty,
        submit,
        reset,
      }}
    >
      <form>{children}</form>
    </FormContext.Provider>
  );
};

export default FormComponent;
