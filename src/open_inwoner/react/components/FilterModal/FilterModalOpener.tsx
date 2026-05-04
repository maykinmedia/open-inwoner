import { withContextGuard } from '@react/lib/hooks/withContextGuard';
import { useModalContext, useRequiredModalContext } from '../Modal/context';
import { useFormContext } from '../Form/context';

/**
 * oip-filter-modal-opener
 *
 * Mobile-only button that opens the oip-filter-modal bottom sheet.
 * Hidden on desktop (≥768 px) via CSS — use oip-filter-bar for desktop.
 *
 * Shows a checkmark indicator when at least one filter is active. The
 * FormContext check is optional: if the component is used outside an
 * oip-form tree the indicator is simply omitted.
 *
 * Must be rendered inside oip-modal (ModalContext).
 */
const FilterModalOpener = withContextGuard(useModalContext, ({ children }) => {
  const { open } = useRequiredModalContext();
  const formCtx = useFormContext();
  const isFiltered = formCtx ? !formCtx.isEmpty.value : false;

  return (
    <button class="oip-filter-modal-opener__button" onClick={open}>
      <material-icon name="filter_alt" />
      <span class="oip-filter-modal-opener__label">{children}</span>
      {isFiltered && <material-icon name="check" />}
    </button>
  );
});

export default FilterModalOpener;
