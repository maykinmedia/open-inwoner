import { createContext } from 'preact';
import { useContext } from 'preact/hooks';

/**
 * The value shape exposed by FilterContext.
 *
 * FilterContext layers filter-specific behaviour on top of FormContext.
 * It must be rendered inside an oip-form tree (FormContext) and provides:
 *   - A label registry so oip-filter-chips can show human-readable chip text.
 *   - The concrete submit action (URL navigation) that FormContext delegates to.
 *
 * Provided by the FilterProvider component (oip-filters).
 */
export interface FilterContextValue {
  /**
   * Register a human-readable label for a field/value pair.
   *
   * Called by oip-select-option on mount so the label is available before
   * the user interacts with the filter. Registering the same pair more than
   * once (e.g. on re-render) is a no-op if the label has not changed.
   *
   * @param fieldName - The `name` attribute of the parent oip-select.
   * @param value     - The raw option value (e.g. `"development"`).
   * @param label     - The display string (e.g. `"Development"`).
   */
  registerLabel: (fieldName: string, value: string, label: string) => void;

  /**
   * Look up the display label for a field/value pair.
   *
   * Returns the label previously registered via `registerLabel`. Falls back
   * to the raw `value` string if no label was registered, ensuring chips are
   * always readable even when label registration is incomplete.
   *
   * @param fieldName - The `name` attribute of the oip-select field.
   * @param value     - The raw option value to look up.
   */
  getLabel: (fieldName: string, value: string) => string;

  /**
   * Submit the filter form.
   *
   * Internally calls `formCtx.submit` with a handler that serialises the
   * current field values into URL query parameters and performs a GET
   * navigation to the updated URL. Multiple selected values for the same
   * field are emitted as repeated params (e.g. `?status=open&status=closed`).
   *
   * Called by oip-form-button when the user confirms their selection.
   */
  submit: () => void;
}

export const FilterContext = createContext<FilterContextValue | null>(null);

/** Returns the nearest FilterContext value, or `null` if outside oip-filters. */
export const useFilterContext = (): FilterContextValue | null =>
  useContext(FilterContext);

/**
 * Returns the nearest FilterContext value.
 * Throws a descriptive error if called outside an oip-filters tree.
 */
export const useRequiredFilterContext = (): FilterContextValue => {
  const ctx = useContext(FilterContext);
  if (!ctx) throw new Error('Component must be nested inside oip-filters');
  return ctx;
};
