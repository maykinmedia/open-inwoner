import { computed, useSignal } from '@preact/signals';
import isEqual from 'lodash/isEqual';
import mapValues from 'lodash/mapValues';
import xor from 'lodash/xor';
import { type AnyComponent as AC } from 'preact';
import { useRef } from 'preact/hooks';
import { FormContext, type FormFieldBinding } from './context';

/**
 * oip-form
 *
 * Root form context provider. Manages all field value state and exposes a
 * generic submit mechanism. Does not perform any navigation or side effects
 * itself — those are the responsibility of the FilterProvider (oip-filters).
 *
 * Renders a plain `<form>` element around its children so that native browser
 * form semantics (e.g. keyboard submission via Enter) are preserved.
 *
 * Provides FormContext to all descendants.
 */
const Form: AC<{}> = ({ children }) => {
  const values = useSignal<Record<string, string[]>>({});
  const initial = useRef<Record<string, string[]>>({});
  const bindings = useRef<Record<string, FormFieldBinding>>({});

  const isDirty = computed(() => !isEqual(values.value, initial.current));
  const isEmpty = computed(() =>
    Object.values(values.value).every((v) => v.length === 0)
  );

  /**
   * Register a field with the form.
   *
   * On the first call for a given `name` the field is initialised with
   * `defaultValue` (or `[]`) and tracked as the initial state. Subsequent
   * calls for the same name return the cached binding so multiple renders of
   * the same field share one reactive value.
   *
   * @param name         - Unique field identifier, matches the HTML `name` attribute.
   * @param defaultValue - Initial selected values; used to compute `isDirty`.
   */
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
        onChange: (value: string, multiple: boolean) => {
          const current = values.value[name] ?? [];
          const next = multiple ? xor(current, [value]) : [value];
          values.value = { ...values.value, [name]: next };
        },
      };
    }
    return bindings.current[name];
  };

  /**
   * Remove a single value from a field's selection.
   *
   * Used by oip-filter-chips when the user clicks the × button on a chip.
   * Has no effect if the value is not currently selected.
   *
   * @param fieldName - The field to mutate.
   * @param value     - The individual value to remove.
   */
  const removeValue = (fieldName: string, value: string): void => {
    const current = values.value[fieldName] ?? [];
    values.value = {
      ...values.value,
      [fieldName]: current.filter((v) => v !== value),
    };
  };

  /**
   * Toggle a single value within a field.
   *
   * In multi-select mode the value is added when absent or removed when
   * present (XOR semantics). In single-select mode the value replaces any
   * existing selection.
   *
   * @param fieldName - The field to mutate.
   * @param value     - The value to toggle.
   * @param multiple  - `true` for checkbox semantics, `false` for radio semantics.
   */
  const toggle = (
    fieldName: string,
    value: string,
    multiple: boolean
  ): void => {
    const current = values.value[fieldName] ?? [];
    const next = multiple ? xor(current, [value]) : [value];
    values.value = { ...values.value, [fieldName]: next };
  };

  /**
   * Reset all fields to empty.
   *
   * Clears every field's selection to `[]`. The initial state snapshot is
   * preserved so `isDirty` becomes `true` if any field had a default value.
   */
  const reset = (): void => {
    values.value = mapValues(values.value, () => []);
  };

  /**
   * Invoke a submit handler with the current field values.
   *
   * The form itself performs no navigation or side-effects. The caller
   * (typically FilterProvider) supplies `fn` which receives a snapshot of
   * all current `{ fieldName: string[] }` values and is responsible for
   * acting on them (e.g. building a query string and navigating).
   *
   * @param fn - Handler called with a copy of the current form values.
   */
  const submit = (fn: (values: Record<string, string[]>) => void): void => {
    fn(values.value);
  };

  return (
    <FormContext.Provider
      value={{
        register,
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

export default Form;
