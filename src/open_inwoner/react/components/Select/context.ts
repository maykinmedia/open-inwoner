import { createContext } from 'preact';
import { useContext } from 'preact/hooks';

export interface SelectContextValue {
  name: string;
  multiple: boolean;
  selectedValues: string[];
  register: (value: string, label: string, initialSelected?: boolean) => void;
  toggle: (value: string) => void;
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
