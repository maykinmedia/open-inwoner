import { type ReadonlySignal } from '@preact/signals';
import { createContext } from 'preact';
import { useContext } from 'preact/hooks';

/**
 * Reactive binding for a single named form field.
 *
 * Returned by `FormContextValue.register` and kept stable across renders.
 * Components that render individual options (oip-select-option) consume this
 * to read and mutate a field's selected values reactively.
 */
export interface FormFieldBinding {
  /**
   * Reactive signal of the field's currently selected values.
   * Subscribe to this in render functions to re-render when the selection
   * changes (Preact Signals integration handles this automatically).
   */
  value: ReadonlySignal<string[]>;

  /**
   * Replace the field's selection with an entirely new set of values.
   * Prefer `onChange` for toggling individual values; use `setValue` when
   * you need to set the selection from an external source (e.g. URL state).
   *
   * @param values - The new complete selection for this field.
   */
  setValue: (values: string[]) => void;

  /**
   * Toggle a single value in the field.
   *
   * In multi-select mode the value is XOR-toggled (added if absent, removed
   * if present). In single-select mode the value replaces the current
   * selection entirely.
   *
   * @param value    - The option value to toggle.
   * @param multiple - `true` for checkbox semantics, `false` for radio.
   */
  onChange: (value: string, multiple: boolean) => void;
}

/**
 * The value shape exposed by FormContext.
 *
 * FormContext is the single source of truth for all field values within
 * an oip-form tree. It intentionally knows nothing about labels, chip
 * rendering, or navigation — those concerns belong to FilterContext.
 */
export interface FormContextValue {
  /**
   * Bind a named field to the form.
   *
   * On first call for a given `name` the field is initialised with
   * `defaultValue` (falling back to `[]`) and that value is stored as the
   * initial snapshot used to compute `isDirty`. Subsequent calls for the same
   * `name` return the same stable binding object, so multiple renders of the
   * same oip-select share one signal.
   *
   * @param name         - Unique field name; should match the HTML `name` attr.
   * @param defaultValue - Pre-selected values to initialise the field with.
   */
  register: (name: string, defaultValue?: string[]) => FormFieldBinding;

  /**
   * Reactive map of all currently selected values keyed by field name.
   *
   * Read this signal to observe the combined form state across all fields.
   * Shape: `{ [fieldName]: string[] }`.
   */
  values: ReadonlySignal<Record<string, string[]>>;

  /**
   * Remove a single value from a field's current selection.
   *
   * Intended for oip-filter-chips so users can deselect individual values
   * via the chip × button without clearing the whole field.
   *
   * @param fieldName - The name of the field to mutate.
   * @param value     - The individual value to remove.
   */
  removeValue: (fieldName: string, value: string) => void;

  /**
   * Toggle a single value within a field.
   *
   * In multi-select mode: XOR toggle (adds when absent, removes when present).
   * In single-select mode: replaces the current selection.
   *
   * @param fieldName - The field to mutate.
   * @param value     - The value to toggle.
   * @param multiple  - `true` for checkbox semantics, `false` for radio.
   */
  toggle: (fieldName: string, value: string, multiple: boolean) => void;

  /**
   * `true` when the current selection differs from the initial (page-load) state.
   *
   * Used by oip-form-button to enable itself only after the user has made
   * changes, preventing redundant submissions.
   */
  isDirty: ReadonlySignal<boolean>;

  /**
   * `true` when every field has an empty selection (`[]`).
   *
   * Used by oip-filter-chips to hide itself when nothing is active.
   */
  isEmpty: ReadonlySignal<boolean>;

  /**
   * Invoke a submit handler with the current form values.
   *
   * The form itself is deliberately side-effect free. The caller — typically
   * the FilterProvider — passes `fn`, which receives a snapshot of all
   * current `{ fieldName: string[] }` pairs and is responsible for acting on
   * them (e.g. serialising to URL query params and navigating).
   *
   * @param fn - Callback that receives the current values and performs the submit action.
   */
  submit: (fn: (values: Record<string, string[]>) => void) => void;

  /**
   * Reset all fields to an empty selection.
   *
   * Sets every field value to `[]`. The initial snapshot is preserved, so
   * `isDirty` will become `true` for any field that had a non-empty default.
   */
  reset: () => void;
}

export const FormContext = createContext<FormContextValue | null>(null);

/** Returns the nearest FormContext value, or `null` if outside oip-form. */
export const useFormContext = (): FormContextValue | null =>
  useContext(FormContext);

/**
 * Returns the nearest FormContext value.
 * Throws a descriptive error if called outside an oip-form tree.
 */
export const useRequiredFormContext = (): FormContextValue => {
  const ctx = useContext(FormContext);
  if (!ctx) throw new Error('Component must be nested inside oip-form');
  return ctx;
};
