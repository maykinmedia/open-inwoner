import { createContext } from 'preact';
import { useContext } from 'preact/hooks';

export interface OptionBinding {
  isSelected: boolean;
  onChange: () => void;
  moveFocus: (direction: 'next' | 'prev') => void;
  close: () => void;
  /** Handle a single printable character for typeahead search. */
  typeahead: (key: string) => void;
}

export interface SelectContextValue {
  /** Field name — used for the HTML input name attribute. */
  name: string;
  /** Whether the field is multi-select (checkbox) or single-select (radio). */
  multiple: boolean;
  /** Close the dropdown and return focus to the toggle button. */
  close: () => void;
  /**
   * Register an option's label and receive back everything needed to render it.
   * Safe to call on every render - re-registration is guarded internally.
   */
  registerOption: (value: string, label: string) => OptionBinding;
}

export const SelectContext = createContext<SelectContextValue | null>(null);

export const useSelectContext = (): SelectContextValue => {
  const ctx = useContext(SelectContext);
  if (!ctx)
    throw new Error('useSelectContext must be used within a Select component');
  return ctx;
};

/** Returns the nearest SelectContext value, or `null` if outside oip-select. */
export const useSelectContextNullable = (): SelectContextValue | null =>
  useContext(SelectContext);
