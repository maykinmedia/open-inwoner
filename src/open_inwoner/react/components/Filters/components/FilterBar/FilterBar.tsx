import { Button } from '@react/components/Button';
import { MaterialIcon } from '@react/components/MaterialIcon';
import { useIsMobile } from '@react/lib/hooks/useIsMobile';
import clsx from 'clsx';
import type { AnyComponent as AC } from 'preact';
import { useState } from 'preact/hooks';
import { FormattedMessage } from 'react-intl';
import { FilterModal, useFilterContext } from '../..';
import './FilterBar.scss';

export interface IFilterBarProps {}

const FilterBar: AC<IFilterBarProps> = ({ children }) => {
  const { isFiltered, isDirty, applyFilters } = useFilterContext();

  const isMobile = useIsMobile();
  const [isModalOpen, setIsModalOpen] = useState(false);

  const openModal = () => setIsModalOpen(true);
  const closeModal = () => setIsModalOpen(false);

  return (
    <>
      {/* MOBILE: Filter button to open modal */}
      {isMobile && (
        <div className={clsx('oip-filter-bar', 'oip-filter-bar--mobile')}>
          <Button
            variant="primary"
            handleClick={openModal}
            transparent
            iconSize="lg"
            underline="none"
          >
            <MaterialIcon name="filter_alt" />
            <span class="button__inner-text">
              <FormattedMessage
                id="filter.mobile_heading"
                description="The title of the mobile dialog filters"
                defaultMessage="Filters"
              />
            </span>
            {isFiltered && <MaterialIcon name="check" />}
          </Button>
        </div>
      )}

      {/* DESKTOP: Inline filter bar */}
      {!isMobile && (
        <div className={clsx('oip-filter-bar', 'oip-filter-bar--desktop')}>
          <span class="oip-filter-bar__label">
            <FormattedMessage
              id="filter.heading"
              description="The title of the filters"
              defaultMessage="Filter op:"
            />
          </span>

          {/* FILTERS */}
          <div class="oip-filter-bar__filters">
            {children}
            <Button
              variant="primary"
              handleClick={applyFilters}
              iconSize="lg"
              underline="none"
              disabled={!isDirty}
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

      {/* MOBILE: Modal */}
      {isMobile && isModalOpen && (
        <FilterModal onClose={closeModal}>{children}</FilterModal>
      )}
    </>
  );
};

export default FilterBar;
