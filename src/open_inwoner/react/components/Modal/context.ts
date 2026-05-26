import { createContext } from 'preact';
import { useContext } from 'preact/hooks';
import { withContextGuard } from '@react/lib/hooks/withContextGuard';

export interface ModalContextValue {
  /** Open the modal by calling showModal() on the <dialog> owned by oip-modal. */
  open: () => void;

  /** Close the modal by calling close() on the <dialog> owned by oip-modal. */
  close: () => void;
}

export const ModalContext = createContext<ModalContextValue | null>(null);

/** Returns the nearest ModalContext value, or `null` if outside oip-modal. */
export const useModalContext = (): ModalContextValue | null =>
  useContext(ModalContext);

/**
 * Returns the nearest ModalContext value.
 * Throws a descriptive error if called outside an oip-modal tree.
 */
export const useRequiredModalContext = (): ModalContextValue => {
  const ctx = useContext(ModalContext);
  if (!ctx) throw new Error('Component must be nested inside oip-modal');
  return ctx;
};

/**
 * Renders children only once ModalContext is available.
 * Returns `null` silently during the async web-component context propagation window.
 */
export const withModalGuard = <P extends {}>(
  Component: import('preact').AnyComponent<P>
) => withContextGuard(useModalContext, Component);
