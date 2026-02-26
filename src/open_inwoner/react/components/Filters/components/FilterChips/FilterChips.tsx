import { Button } from '@react/components/Button';
import { AnyComponent as AC } from 'preact';
import { FormattedMessage } from 'react-intl';
import { FilterChip, useFilterContext } from '../..';
import './FilterChips.scss';

export interface FilterChipsProps {
  showClearAll?: boolean;
}

const FilterChips: AC<FilterChipsProps> = ({ showClearAll = true }) => {
  const {
    filterGroups,
    selectedFilters,
    isFiltered,
    toggleValue,
    clearAllFilters,
  } = useFilterContext();

  // Don't render if no filters are selected
  if (!isFiltered) return null;

  return (
    <div className="oip-filter-chips">
      {filterGroups.map((group) =>
        selectedFilters[group.name].map((value) => {
          const choice = group.choices.find((c) => c.value === value);
          if (!choice) return null;
          return (
            <FilterChip
              key={`${group.name}-${value}`}
              groupName={group.name}
              groupLabel={group.label}
              value={choice.value}
              label={choice.label}
              onRemove={toggleValue}
            />
          );
        })
      )}
      {showClearAll && isFiltered && (
        <Button
          handleClick={clearAllFilters}
          className="oip-filter-chips__clear-button"
          variant="primary"
          transparent
        >
          <FormattedMessage
            id="filter.clear_all"
            description="The label of the 'clear all' button."
            defaultMessage="Filters wissen"
          >
            {(text) => <span class="button__inner-text">{text}</span>}
          </FormattedMessage>
        </Button>
      )}
    </div>
  );
};
export default FilterChips;
