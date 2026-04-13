import { useSignal, useComputed } from '@preact/signals';
import { useContext } from 'preact/hooks';
import { SignalTestContext } from '../NewFilter/context';
import type { ModalContextValue } from './context';

export interface UseModalProviderOptions {
  /** Called when the modal should close (e.g. backdrop click, close button). */
  onClose: () => void;
}

/**
 * Encapsulates all state and bridge logic for Modal.
 *
 * - Reads from SignalTestContext when present (nested inside oip-sig-root-test).
 * - Falls back to own signal state when used standalone.
 * - Returns the full ModalContextValue so Modal.tsx only needs to provide
 *   context and render markup.
 */
export const useModalProvider = ({
  onClose,
}: UseModalProviderOptions): ModalContextValue => {
  const rootCtx = useContext(SignalTestContext);

  // Own state — used when no root context is present.
  const ownSelected = useSignal<Record<string, string[]>>({});
  const ownInitial = useSignal<Record<string, string[]>>({});

  const ownIsDirty = useComputed(
    () => JSON.stringify(ownSelected.value) !== JSON.stringify(ownInitial.value)
  );

  const isDirty = rootCtx ? rootCtx.isDirty : ownIsDirty;

  const apply = () => {
    if (rootCtx) {
      rootCtx.applyFilters();
    } else {
      ownInitial.value = { ...ownSelected.value };
    }
    onClose();
  };

  const clear = () => {
    if (rootCtx) {
      rootCtx.clearAll();
    } else {
      ownSelected.value = {};
    }
  };

  return {
    isDirty,
    close: onClose,
    apply,
    clear,
  };
};
