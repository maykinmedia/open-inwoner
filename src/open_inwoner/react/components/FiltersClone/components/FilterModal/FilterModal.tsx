import { Button } from '@react/components/Button';
import { MaterialIcon } from '@react/components/MaterialIcon';
import type { AnyComponent } from 'preact';
import { FormattedMessage } from 'react-intl';
import { useFilterContext } from '../..';
import './FilterModal.scss';

export interface IFilterModalProps {
  onClose: () => void;
}

/**
 * FilterModal - Full-screen modal for mobile filter selection
 *
 * Must be used within a FilterWrapper.
 */
const FilterModal: AnyComponent<IFilterModalProps> = ({
  onClose,
  children,
}) => {
  const { clearAllFilters, applyFilters, isDirty } = useFilterContext();

  const handleApply = () => {
    applyFilters();
    onClose();
  };

  return (
    <div
      class="oip-filter-modal__backdrop"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div class="oip-filter-modal">
        <header class="oip-filter-modal__header">
          <div class="oip-filter-modal__header-actions">
            <Button
              title="Sluiten"
              variant="primary"
              handleClick={onClose}
              transparent
              className={'oip-filter-modal__close'}
            >
              <MaterialIcon name="close" />
            </Button>
            <Button
              text="Wis alle filters"
              variant="primary"
              handleClick={clearAllFilters}
              transparent
            />
          </div>
          <h2 class="oip-filter-modal__heading">
            <FormattedMessage
              id="filter.mobile_title"
              description="The title of the mobile dialog filters"
              defaultMessage="Filters"
            />
          </h2>
        </header>

        {/* FILTERS */}
        <div class="oip-filter-modal__content">{children}</div>

        <div class="oip-filter-modal__footer">
          <Button
            variant="primary"
            handleClick={handleApply}
            disabled={!isDirty}
            fullWidth
          >
            <span class="button__inner-text">
              <FormattedMessage
                id="filter.show_results"
                description="Show results text"
                defaultMessage="Toon resultaten"
              />
            </span>
          </Button>
        </div>
      </div>
    </div>
  );
};

export default FilterModal;
