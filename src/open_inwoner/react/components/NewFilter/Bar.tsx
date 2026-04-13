import { MaterialIcon } from '@react/components/MaterialIcon';
import { Button } from '../Button';
import { useIsMobile } from '@react/lib/hooks/useIsMobile';
import clsx from 'clsx';
import { type AnyComponent as AC } from 'preact';
import { useState } from 'preact/hooks';
import { FormattedMessage } from 'react-intl';
import { useSignalTest } from './context';
import FilterModal from '../Modal/Modal';

export interface FilterBarProps {}

/**
 * oip-filter-bar-test
 * Desktop: wraps filter groups in an inline bar with a "Toon resultaten" button.
 * Mobile: shows a "Filters" button that opens a FilterModal with the same groups.
 */
const FilterBar: AC<FilterBarProps> = ({ children }) => {
  const { isDirty, isFiltered, applyFilters } = useSignalTest();
  const isMobile = useIsMobile();
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      {/* MOBILE: button to open modal */}
      {isMobile && (
        <div class={clsx('oip-filter-bar', 'oip-filter-bar--mobile')}>
          <button
            type="button"
            class="oip-filter-bar__mobile-button"
            onClick={() => setIsModalOpen(true)}
          >
            <FormattedMessage
              id="filter.mobile_heading"
              description="The title of the mobile dialog filters"
              defaultMessage="Filters"
            />
            {isFiltered.value && <MaterialIcon name="check" />}
          </button>
        </div>
      )}

      {/* DESKTOP: inline bar */}
      {!isMobile && (
        <div class={clsx('oip-filter-bar', 'oip-filter-bar--desktop')}>
          <span class="oip-filter-bar__label">
            <FormattedMessage
              id="filter.heading"
              description="The title of the filters"
              defaultMessage="Filter op:"
            />
          </span>
          <div class="oip-filter-bar__filters">
            {children}
            <Button
              variant="primary"
              handleClick={applyFilters}
              iconSize="lg"
              underline="none"
              disabled={!isDirty.value}
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
      )}

      {/* MOBILE: modal */}
      {isMobile && isModalOpen && (
        <FilterModal onClose={() => setIsModalOpen(false)}>
          {children}
        </FilterModal>
      )}
    </>
  );
};

export default FilterBar;
