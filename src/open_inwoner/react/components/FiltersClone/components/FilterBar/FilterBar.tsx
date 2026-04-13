import { Button } from '@react/components/Button';
import { MaterialIcon } from '@react/components/MaterialIcon';
import { useIsMobile } from '@react/lib/hooks/useIsMobile';
import clsx from 'clsx';
import type { AnyComponent as AC } from 'preact';
import { useState } from 'preact/hooks';
import { FormattedMessage } from 'react-intl';
import { FilterModal, useFilterContext } from '../..';
import { FilterGroup } from '../Filter/Filter';
import './FilterBar.scss';

export interface IFilterBarProps {}

/**
 * FilterBar - Web component adapter for `oip-filter-bar`.
 *
 * - Desktop: renders a `<slot>` so composed `oip-filter` elements
 *   are projected inline next to the "Show results" button.
 * - Mobile: renders a trigger button + modal. The modal renders
 *   `FilterGroup` components from `filterGroups` in context so we
 *   don't need to duplicate the slotted content.
 *
 * @example HTML composition:
 * ```html
 * <oip-filters data-id="filters-data">
 *   <oip-filter-bar>
 *     <oip-filter name="category"></oip-filter>
 *     <oip-filter name="tags"></oip-filter>
 *   </oip-filter-bar>
 * </oip-filters>
 * ```
 */
const FilterBar: AC<IFilterBarProps> = ({ children }) => {
  const { isFiltered, isDirty, applyFilters, filterGroups } =
    useFilterContext();

  const isMobile = useIsMobile();
  const [isModalOpen, setIsModalOpen] = useState(false);

  const openModal = () => setIsModalOpen(true);
  const closeModal = () => setIsModalOpen(false);

  return (
    <div>
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
            {isFiltered.value && <MaterialIcon name="check" />}
          </Button>
        </div>
      )}

      {/* DESKTOP: Inline filter bar with slotted oip-filter elements */}
      {!isMobile && (
        <div className={clsx('oip-filter-bar', 'oip-filter-bar--desktop')}>
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

      {/* MOBILE: Modal renders FilterGroup from context (can't duplicate slot content) */}
      {isMobile && isModalOpen && (
        <FilterModal onClose={closeModal}>
          {filterGroups
            .filter((group) => group.choices.length > 0)
            .map((group) => (
              <FilterGroup key={group.name} {...group} />
            ))}
        </FilterModal>
      )}
    </div>
  );
};

export default FilterBar;
