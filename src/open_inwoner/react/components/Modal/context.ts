import type { ReadonlySignal } from '@preact/signals';
import { createContext } from 'preact';
import { useContext } from 'preact/hooks';

export interface ModalContextValue {
  /** True when the current selection differs from the page-load state. */
  isDirty: ReadonlySignal<boolean>;
  /** Close the modal without applying changes. */
  close: () => void;
  /** Apply the current filters and close the modal. */
  apply: () => void;
  /** Clear all selections. */
  clear: () => void;
}

export const ModalContext = createContext<ModalContextValue | null>(null);

export const useModalContext = (): ModalContextValue => {
  const ctx = useContext(ModalContext);
  if (!ctx)
    throw new Error('useModalContext must be used within a Modal component');
  return ctx;
};
