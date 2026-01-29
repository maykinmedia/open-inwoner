import clsx from 'clsx';
import { AnyComponent as AC } from 'preact';
import { useState, useEffect, useRef } from 'preact/hooks';
import { MaterialIcon } from '../MaterialIcon';
import { getDynamicPeriodOptions } from './dynamic-period-options';
import './FiltersBar.scss';

export interface IFilterChoice {
  value: string;
  label: string;
}

export interface IFilterGroup {
  name: string;
  label: string;
  choices: IFilterChoice[];
}

export interface IFiltersBarProps {
  currentUrl?: string;
  baseUrl?: string;
  addDynamicPeriods?: boolean;
}

const FiltersBar: AC<IFiltersBarProps> = ({
  currentUrl = '',
  baseUrl = '',
  addDynamicPeriods = false,
}) => {
  const [element, setElement] = useState<HTMLElement | null>(null);
  const [filterGroups, setFilterGroups] = useState<IFilterGroup[]>([]);
  const [selectedFilters, setSelectedFilters] = useState<
    Record<string, string[]>
  >({});
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const dropdownRefs = useRef<Record<string, HTMLDivElement | null>>({});

  // Capture the actual DOM element when component mounts
  useEffect(() => {
    setTimeout(() => {
      const filtersBar = document.querySelector('oip-filters-bar');
      if (filtersBar) {
        console.log('FiltersBar: Found oip-filters-bar element in DOM');
        setElement(filtersBar as HTMLElement);
      } else {
        console.error('FiltersBar: Could not find oip-filters-bar element');
      }
    }, 0);
  }, []);

  // Parse filter attributes from the custom element
  useEffect(() => {
    if (!element) {
      console.log('FiltersBar: element not set yet');
      return;
    }

    console.log('FiltersBar: Parsing attributes from element');
    const attributes = Array.from(element.attributes);
    console.log('FiltersBar: Total attributes:', attributes.length);

    // Check if dynamic periods should be added
    // Data attributes come as strings, so convert "true" to boolean
    const shouldAddDynamicPeriods =
      addDynamicPeriods === true ||
      element.getAttribute('data-add-dynamic-periods') === 'true';
    console.log(
      'FiltersBar: shouldAddDynamicPeriods:',
      shouldAddDynamicPeriods
    );

    const groups: Record<number, IFilterGroup> = {};
    const selected: Record<string, string[]> = {};

    // Parse current URL to get active filters
    const urlParams = new URLSearchParams(
      new URL(currentUrl || window.location.href).search
    );

    // Parse all data-filter-* attributes
    attributes.forEach((attr) => {
      const match = attr.name.match(/^data-filter-(\d+)-(.+)$/);
      if (!match) return;

      console.log('FiltersBar: Processing attribute:', attr.name);
      const [, groupNum, rest] = match;
      const groupIndex = parseInt(groupNum);

      // Initialize group if not exists
      if (!groups[groupIndex]) {
        groups[groupIndex] = { name: '', label: '', choices: [] };
      }

      // Parse name and label
      if (rest === 'name') {
        groups[groupIndex].name = attr.value;
        selected[attr.value] = [];
      } else if (rest === 'label') {
        groups[groupIndex].label = attr.value;
      } else {
        // Parse choices
        const choiceMatch = rest.match(/^choice-(\d+)-(value|label)$/);
        if (choiceMatch) {
          const [, choiceNum, type] = choiceMatch;
          const choiceIndex = parseInt(choiceNum);

          if (!groups[groupIndex].choices[choiceIndex - 1]) {
            groups[groupIndex].choices[choiceIndex - 1] = {
              value: '',
              label: '',
            };
          }

          if (type === 'value') {
            groups[groupIndex].choices[choiceIndex - 1].value = attr.value;
          } else {
            groups[groupIndex].choices[choiceIndex - 1].label = attr.value;
          }
        }
      }
    });

    // Convert to array and sort by group number
    let sortedGroups = Object.values(groups).filter((g) => g.name && g.label);
    console.log('FiltersBar: Parsed groups:', sortedGroups);

    // Add dynamic period options if enabled
    if (shouldAddDynamicPeriods) {
      console.log('FiltersBar: Adding dynamic period options');
      sortedGroups = sortedGroups.map((group) => {
        if (group.name === 'periode') {
          const dynamicOptions = getDynamicPeriodOptions('nl');
          console.log('FiltersBar: Dynamic options:', dynamicOptions);
          return {
            ...group,
            choices: [...dynamicOptions, ...group.choices],
          };
        }
        return group;
      });
    }

    // Initialize selected filters from URL params
    sortedGroups.forEach((group) => {
      const urlValues = urlParams.getAll(group.name);
      if (urlValues.length > 0) {
        selected[group.name] = urlValues;
      } else {
        selected[group.name] = [];
      }
    });

    console.log('FiltersBar: Selected filters:', selected);
    setFilterGroups(sortedGroups);
    setSelectedFilters(selected);
  }, [element, currentUrl, addDynamicPeriods]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const isClickInside = Object.values(dropdownRefs.current).some(
        (ref) => ref && ref.contains(target)
      );

      if (!isClickInside && openDropdown && openDropdown !== 'mobile') {
        setOpenDropdown(null);
      }
    };

    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [openDropdown]);

  const handleCheckboxChange = (
    groupName: string,
    value: string,
    checked: boolean
  ) => {
    setSelectedFilters((prev) => {
      const updated = { ...prev };
      if (checked) {
        // Add to selected (cumulative)
        if (!updated[groupName].includes(value)) {
          updated[groupName] = [...updated[groupName], value];
        }
      } else {
        // Remove from selected
        updated[groupName] = updated[groupName].filter((v) => v !== value);
      }
      return updated;
    });
  };

  const handleApplyFilters = () => {
    // Build URL with selected filters
    const params = new URLSearchParams(
      new URL(baseUrl || window.location.href).search
    );

    // Clear existing filter params
    filterGroups.forEach((group) => {
      params.delete(group.name);
    });

    // Add selected filters (cumulative, can have multiple per group)
    Object.entries(selectedFilters).forEach(([groupName, values]) => {
      values.forEach((value) => {
        params.append(groupName, value);
      });
    });

    const newUrl = `${baseUrl}?${params.toString()}`;
    console.log('FiltersBar: New URL:', newUrl);
    window.history.pushState({}, '', newUrl);
    window.location.reload();

    setOpenDropdown(null);
  };

  const handleReset = () => {
    console.log('FiltersBar: handleReset called');
    console.log('FiltersBar: Current selectedFilters:', selectedFilters);
    const resetFilters: Record<string, string[]> = {};
    filterGroups.forEach((group) => {
      resetFilters[group.name] = [];
    });
    console.log('FiltersBar: Setting resetFilters:', resetFilters);
    setSelectedFilters(resetFilters);
    console.log('FiltersBar: Reset complete');
  };

  const calculateTotalResults = () => {
    const totalSelected = Object.values(selectedFilters).reduce(
      (sum, values) => sum + values.length,
      0
    );
    return totalSelected > 0 ? totalSelected : 0;
  };

  const isFiltered = Object.values(selectedFilters).some(
    (values) => values.length > 0
  );

  console.log(
    'FiltersBar: Rendering, groups:',
    filterGroups.length,
    'selected:',
    selectedFilters
  );

  return (
    <>
      {/* DESKTOP: Inline filter bar */}
      <div class="oip-filters-bar--desktop">
        <form
          class="form oip-filters-bar__form"
          method="GET"
          id="filters-bar-form"
          noValidate
        >
          <span class="oip-filters-bar__label">Filter op:</span>

          <div class="oip-filters-bar__filters">
            {filterGroups.map((group) => (
              <div
                key={group.name}
                class="oip-filters-bar__filter-group"
                ref={(el) => {
                  if (el) dropdownRefs.current[group.name] = el;
                }}
              >
                <button
                  type="button"
                  class={clsx('button oip-filters-bar__dropdown-button', {
                    'oip-filters-bar__dropdown-button--active':
                      selectedFilters[group.name]?.length > 0,
                  })}
                  onClick={() =>
                    setOpenDropdown(
                      openDropdown === group.name ? null : group.name
                    )
                  }
                  aria-haspopup="listbox"
                  aria-expanded={openDropdown === group.name ? 'true' : 'false'}
                  title={group.label}
                >
                  <span class="oip-filters-bar__dropdown-label">
                    {selectedFilters[group.name]?.length > 0
                      ? `${group.label} (${selectedFilters[group.name].length})`
                      : group.label}
                  </span>
                  <MaterialIcon name="expand_more" />
                </button>

                {/* Dropdown Content */}
                {openDropdown === group.name && (
                  <div
                    class="oip-filters-bar__dropdown-content"
                    role="listbox"
                    aria-labelledby={`filter-${group.name}`}
                  >
                    <div class="oip-filters-bar__dropdown-scroll">
                      {group.choices.map((choice) => (
                        <label
                          key={choice.value}
                          class="oip-filters-bar__checkbox-wrapper"
                          role="option"
                          aria-selected={selectedFilters[group.name]?.includes(
                            choice.value
                          )}
                        >
                          <input
                            type="checkbox"
                            class="checkbox__input"
                            name={group.name}
                            value={choice.value}
                            checked={
                              selectedFilters[group.name]?.includes(
                                choice.value
                              ) || false
                            }
                            onChange={(e) =>
                              handleCheckboxChange(
                                group.name,
                                choice.value,
                                (e.target as HTMLInputElement).checked
                              )
                            }
                          />
                          <span class="checkbox__label">
                            <span>{choice.label}</span>
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Desktop: Reset button */}
          <div class="oip-filters-bar__reset--desktop">
            <button
              type="button"
              class={clsx('button button--primary button--transparent', {
                hide: !isFiltered,
              })}
              onClick={handleReset}
              title="Wis alle filters"
              aria-label="Wis alle filters"
            >
              <span class="button__inner-text">Wis alle filters</span>
            </button>
          </div>

          {/* Desktop: Apply button */}
          <button
            type="button"
            class="button button--primary oip-filters-bar__apply-button--desktop"
            onClick={handleApplyFilters}
            title="Toon resultaten"
          >
            Toon resultaten
          </button>
        </form>
      </div>

      {/* MOBILE: Filter button to open modal */}
      <div class="oip-filters-bar--mobile-button">
        <div class="oip-filters-bar__mobile-button-content">
          <p class="utrecht-paragraph oip-filters-bar__heading">Filters</p>
          <div
            class={clsx('oip-filters-bar__mobile-selection', {
              active: isFiltered,
            })}
          >
            <button
              type="button"
              class="button button--transparent oip-filters-bar__open-button"
              onClick={() => setOpenDropdown('mobile')}
              title="Filters"
              aria-label="Filters"
            >
              <MaterialIcon name="filter_alt" />
              <span class="button__inner-text">Filters</span>
            </button>
            {isFiltered && (
              <>
                <MaterialIcon name="check" />
                <span class="sr-only">Gekozen filters</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* MOBILE: Modal with backdrop */}
      {openDropdown === 'mobile' && (
        <div class="oip-filters-bar__backdrop">
          <div class="oip-filters-bar--mobile">
            {/* Mobile Header */}
            <div class="oip-filters-bar__mobile-header">
              <h2 class="oip-filters-bar__heading">Filters</h2>
              <div class="oip-filters-bar__mobile-header-actions">
                <button
                  type="button"
                  class="button button--primary button--transparent"
                  onClick={handleReset}
                  title="Annuleren"
                  aria-label="Annuleren"
                >
                  Annuleren
                </button>
                <button
                  type="button"
                  class="button oip-filters-bar__close button--textless button--icon button--transparent"
                  onClick={() => setOpenDropdown(null)}
                  title="Sluiten"
                  aria-label="Sluiten"
                >
                  <MaterialIcon name="close" />
                </button>
              </div>
            </div>

            {/* Mobile Filter Groups */}
            <div class="oip-filters-bar__mobile-filters">
              {filterGroups.map((group) => (
                <div key={group.name} class="oip-filters-bar__filter-section">
                  <h3 class="oip-filters-bar__filter-section-title">
                    {group.label}
                  </h3>

                  <div class="oip-filters-bar__mobile-choices">
                    {group.choices.map((choice) => (
                      <label
                        key={choice.value}
                        class={clsx('oip-filters-bar__checkbox-wrapper', {
                          'oip-filters-bar__checkbox-wrapper--selected':
                            selectedFilters[group.name]?.includes(choice.value),
                        })}
                      >
                        <input
                          type="checkbox"
                          class="checkbox__input"
                          name={group.name}
                          value={choice.value}
                          checked={
                            selectedFilters[group.name]?.includes(
                              choice.value
                            ) || false
                          }
                          onChange={(e) =>
                            handleCheckboxChange(
                              group.name,
                              choice.value,
                              (e.target as HTMLInputElement).checked
                            )
                          }
                        />
                        <span class="checkbox__label">{choice.label}</span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Mobile Apply Button */}
            <div class="oip-filters-bar__mobile-footer">
              <button
                type="button"
                class="button button--primary"
                onClick={handleApplyFilters}
                title="Toon resultaten"
              >
                Toon {calculateTotalResults()} resultaten
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default FiltersBar;
