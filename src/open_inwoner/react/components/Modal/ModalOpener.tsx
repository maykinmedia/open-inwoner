import { Button } from '@react/components/Button';
import { withModalGuard, useRequiredModalContext } from '../Modal/context';

/**
 * oip-filter-modal-opener
 *
 * Renders the button which opens the modal.
 *
 * Must be rendered inside oip-modal (ModalContext).
 */
const ModalOpener = withModalGuard(({ children }) => {
  const modalCtx = useRequiredModalContext();

  return (
    <Button
      variant="primary"
      handleClick={modalCtx.open}
      transparent
      iconSize="lg"
      underline="none"
      className="oip-modal-opener"
    >
      {children}
    </Button>
  );
});

export default ModalOpener;
