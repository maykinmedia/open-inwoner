import { AnyComponent as AC, createContext } from 'preact';
import { useContext } from 'preact/hooks';
import { withContextGuard } from '@react/lib/hooks/withContextGuard';

export interface FieldsetOptionBinding {
  isSelected: boolean;
  onChange: () => void;
}

/**
 * The value shape exposed by FieldsetContext.
 *
 * Provided by oip-fieldset. Consumed by oip-fieldset-option children to
 * register their labels and read/write the selected state.
 */
export interface FieldsetContextValue {
  /** Field name — used for the HTML input name attribute. */
  name: string;
  /** Whether options are checkboxes (true) or radio buttons (false). */
  multiple: boolean;
  /**
   * Register an option and receive its current binding.
   *
   * Registers the display label with FilterContext for chip rendering and
   * returns the reactive selected state and toggle handler. Safe to call on
   * every render — re-registration is a no-op when label is unchanged.
   *
   * @param value - The raw option value.
   * @param label - The human-readable display label.
   */
  registerOption: (value: string, label: string) => FieldsetOptionBinding;
}

export const FieldsetContext = createContext<FieldsetContextValue | null>(null);

/** Returns the nearest FieldsetContext value, or `null` if outside oip-fieldset. */
export const useFieldsetContext = (): FieldsetContextValue | null =>
  useContext(FieldsetContext);

/**
 * Returns the nearest FieldsetContext value.
 * Throws a descriptive error if called outside an oip-fieldset tree.
 */
export const useRequiredFieldsetContext = (): FieldsetContextValue => {
  const ctx = useContext(FieldsetContext);
  if (!ctx) throw new Error('Component must be nested inside oip-fieldset');
  return ctx;
};

/**
 * Renders children only once FieldsetContext is available.
 * Returns `null` silently during the async web-component context propagation window.
 */
export const withFieldsetGuard = <P extends {}>(Component: AC<P>) =>
  withContextGuard(useFieldsetContext, Component);
