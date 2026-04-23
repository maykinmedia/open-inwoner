import { type ReadonlySignal } from '@preact/signals';
import { createContext } from 'preact';
import { useContext } from 'preact/hooks';

export interface FormFieldBinding {
  /** Reactive selected values for this field. */
  value: ReadonlySignal<string[]>;
  /** Replace the field's selected values. */
  setValue: (values: string[]) => void;
}

export interface FormContextValue {
  /**
   * Bind a named field to the form.
   * The form initialises the field on first call; subsequent calls return the
   * same stable binding. The form tracks values per field but does not
   * enumerate individual options — only the current and initial values.
   */
  register: (name: string, defaultValue?: string[]) => FormFieldBinding;

  /**
   * Register a display label for a value so oip-filter-chips can render it.
   * Called by oip-select when its options mount.
   */
  registerLabel: (fieldName: string, value: string, label: string) => void;

  /** Look up a display label registered via registerLabel, falls back to value. */
  getLabel: (fieldName: string, value: string) => string;

  /** All current selected values keyed by field name. */
  values: ReadonlySignal<Record<string, string[]>>;

  /** Remove a single value from a field — used by oip-filter-chips. */
  removeValue: (fieldName: string, value: string) => void;

  /** Toggle a value in a field. Adds when absent; removes when present (multi). Replaces for single. */
  toggle: (fieldName: string, value: string, multiple: boolean) => void;

  /** True when the current selection differs from the initial (page-load) state. */
  isDirty: ReadonlySignal<boolean>;

  /** True when at least one field has a selected value. */
  isEmpty: ReadonlySignal<boolean>;

  /** Submit: calls form.requestSubmit() on a wrapping <form>, or navigates via URL. */
  submit: () => void;

  /** Reset all fields to empty. */
  reset: () => void;
}

export const FormContext = createContext<FormContextValue | null>(null);

export const useFormContext = (): FormContextValue | null =>
  useContext(FormContext);

export const useRequiredFormContext = (): FormContextValue => {
  const ctx = useContext(FormContext);
  if (!ctx) throw new Error('Component must be nested inside oip-form');
  return ctx;
};
