import { Button } from '@react/components/Button';
import { MaterialIcon } from '@react/components/MaterialIcon';
import { FormattedMessage } from 'react-intl';
import { withModalGuard, useRequiredModalContext } from '../Modal/context';
import { useRequiredFilterContext } from '../Filters/context';
import { useRequiredFormContext } from '../Form/context';

const HEADING_ID = 'oip-filter-modal-heading';

/**
 * oip-filter-modal
 *
 * Full-screen bottom-sheet modal for mobile filter selection.
 * Renders a native <dialog> element — focus trapping, Escape dismissal,
 * and the backdrop are handled by the browser.
 *
 * Must be rendered inside oip-modal (ModalContext), oip-filters (FilterContext),
 * and oip-form (FormContext).
 */
const FilterModal = withModalGuard(({ children }) => {
  const { close } = useRequiredModalContext();
  const formCtx = useRequiredFormContext();
  const filterCtx = useRequiredFilterContext();

  const handleApply = () => {
    filterCtx.submit();
    close();
  };

  return (
    <div>
      <header class="oip-filter-modal__header">
        <div class="oip-filter-modal__header-actions">
          <Button
            autofocus
            variant="primary"
            handleClick={close}
            transparent
            className="oip-filter-modal__close-button"
            title="Sluiten"
          >
            <material-icon name="close" />
          </Button>
          <Button
            variant="primary"
            handleClick={formCtx.reset}
            transparent
            className="oip-filter-modal__reset-button"
          >
            <FormattedMessage
              id="filter.clear_all"
              description="Button to clear all active filters"
              defaultMessage="Wis alle filters"
            />
          </Button>
        </div>
        <h2 id={HEADING_ID} class="oip-filter-modal__heading">
          <FormattedMessage
            id="filter.mobile_title"
            description="The title of the mobile filter dialog"
            defaultMessage="Filters"
          />
        </h2>
      </header>

      <div class="oip-filter-modal__content">{children}</div>

      <div class="oip-filter-modal__footer">
        <Button
          variant="primary"
          handleClick={handleApply}
          disabled={!formCtx.isDirty.value}
          fullWidth
        >
          <FormattedMessage
            id="filter.show_results"
            description="Button to apply filters and show results"
            defaultMessage="Toon resultaten"
          />
        </Button>
      </div>
    </div>
  );
});

export default FilterModal;
