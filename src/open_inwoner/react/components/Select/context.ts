import { createContext } from 'preact';
import { useContext } from 'preact/hooks';

export interface SelectContextValue {
  /** Field name — passed to FormContext when toggling or reading selections. */
  name: string;
  /** Whether the field is multi-select (checkbox) or single-select (radio). */
  multiple: boolean;
  /** Called by each option on mount to register its display label with the form. */
  registerLabel: (value: string, label: string) => void;
  /** Move keyboard focus to the next or previous option. */
  moveFocus: (direction: 'next' | 'prev') => void;
  /** Close the dropdown and return focus to the toggle button. */
  close: () => void;
}

export const SelectContext = createContext<SelectContextValue | null>(null);

export const useSelectContext = (): SelectContextValue => {
  const ctx = useContext(SelectContext);
  if (!ctx)
    throw new Error('useSelectContext must be used within a Select component');
  return ctx;
};
