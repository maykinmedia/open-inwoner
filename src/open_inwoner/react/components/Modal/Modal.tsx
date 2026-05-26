import { ComponentChildren, type AnyComponent as AC } from 'preact';
import { useRef } from 'preact/hooks';
import { ModalContext } from './context';

interface ModalProps {
  opener?: ComponentChildren;
}

const Modal: AC<ModalProps> = ({ opener, children }) => {
  const dialogRef = useRef<HTMLDialogElement>(null);

  const open = () => dialogRef.current?.showModal();
  const close = () => dialogRef.current?.close();

  return (
    <ModalContext.Provider value={{ open, close }}>
      {opener}
      <dialog
        ref={dialogRef}
        onClick={(e) => e.target === e.currentTarget && close()}
        onClose={close}
      >
        {children}
      </dialog>
    </ModalContext.Provider>
  );
};

export default Modal;
