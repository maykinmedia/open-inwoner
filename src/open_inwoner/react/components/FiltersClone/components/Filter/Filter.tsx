import { MaterialIcon } from '@react/components/MaterialIcon';
import { useIsMobile, useOnClickOutside } from '@react/lib/hooks';
import clsx from 'clsx';
import { AnyComponent as AC } from 'preact';
import { type IFilterGroup, useFilterContext } from '../..';
import { useSelect } from '../../hooks/useSelect';
import './Filter.scss';

/**
 * FilterGroup - Internal rendering component for a single filter.
 *
 * Renders differently based on viewport:
 * - Desktop: multi-select dropdown with local open/close state
 * - Mobile: fieldset with title and checkbox/radio list
 *
 * Used directly by FilterBar's mobile modal, and wrapped by the
 * `Filter` web component adapter below.
 */
export const FilterGroup: AC<IFilterGroup> = ({
  name,
  label,
  choices,
  multiple = true,
}) => {
  const { selectedFilters, toggleValue, toggleValueRadio } = useFilterContext();
  const isMobile = useIsMobile();
  const Wrapper = isMobile ? 'fieldset' : 'div';
  const selectedValues = selectedFilters.value[name] || [];
  const selectedCount = selectedValues.length;

  const {
    containerRef,
    isOpen,
    activeIndex,
    handleKeyDown,
    closeDropdown,
    toggleDropdown,
  } = useSelect({ choices, multiple, name, toggleValue, toggleValueRadio });

  console.log(selectedFilters.value);

  const showChoices = isMobile || isOpen;

  // Close dropdown when clicking outside (desktop only)
  useOnClickOutside(containerRef, closeDropdown, isMobile || !isOpen);

  return (
    <Wrapper
      class={clsx(
        'oip-filter',
        isMobile ? 'oip-filter--mobile' : 'oip-filter--dropdown'
      )}
      ref={containerRef as any}
      onKeyDown={isMobile ? undefined : handleKeyDown}
    >
      {isMobile ? (
        <legend className="oip-filter__title" id={`filter-${name}`}>
          {label}
        </legend>
      ) : (
        <button
          type="button"
          className={clsx('oip-filter__button', {
            ['oip-filter__button--open']: showChoices,
          })}
          onClick={toggleDropdown}
          aria-haspopup="listbox"
          aria-expanded={isOpen}
          title={label}
          id={`filter-${name}`}
        >
          <span class="oip-filter__label">
            {selectedCount > 0 ? `${label} (${selectedCount})` : label}
          </span>
          <MaterialIcon name="expand_more" />
        </button>
      )}

      {/* DROPDOWN LIST */}
      {showChoices && (
        <div
          className={'oip-filter__choices'}
          role="listbox"
          aria-labelledby={`filter-${name}`}
          aria-expanded={showChoices}
          aria-activedescendant={
            activeIndex >= 0
              ? `option-${name}-${choices[activeIndex].value}`
              : undefined
          }
        >
          {choices.map((choice, index) => {
            const isChecked = selectedValues.includes(choice.value);

            return (
              <div
                className={clsx('oip-filter__option', {
                  'oip-filter__option--active': index === activeIndex,
                })}
                role="option"
                aria-selected={isChecked}
                key={`${name}.${choice.value}`}
                id={`option-${name}-${choice.value}`}
              >
                <input
                  type={multiple ? 'checkbox' : 'radio'}
                  name={name}
                  class="oip-filter__option-input"
                  id={`${name}.${choice.value}`}
                  value={choice.value}
                  checked={isChecked}
                  tabIndex={isMobile ? undefined : -1}
                  onChange={() => {
                    if (multiple) toggleValue(name, choice.value);
                    else toggleValueRadio(name, choice.value);
                  }}
                />
                <label
                  class="oip-filter__option-label"
                  htmlFor={`${name}.${choice.value}`}
                >
                  <span>{choice.label}</span>
                </label>
              </div>
            );
          })}
        </div>
      )}
    </Wrapper>
  );
};

export interface IFilterProps {
  name: string;
}

/**
 * Filter - Web component adapter for `oip-filter`.
 *
 * Looks up its filter group by `name` from `FiltersContext` and
 * delegates rendering to `FilterGroup`. Fails silently when no
 * matching group or no choices are found.
 *
 * @example HTML composition:
 * ```html
 * <oip-filters data-id="filters-data">
 *   <oip-filter-bar>
 *     <oip-filter name="category"></oip-filter>
 *   </oip-filter-bar>
 * </oip-filters>
 * ```
 */
const Filter: AC<IFilterProps> = ({ name }) => {
  const { filterGroups } = useFilterContext();
  const group = filterGroups.find((g) => g.name === name);

  if (!group || !group.choices.length) return null;

  return <FilterGroup {...group} />;
};

export default Filter;
