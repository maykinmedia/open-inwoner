import { type AnyComponent as AC } from 'preact';
import { useSignalTest } from './context';
import { MaterialIcon } from '../MaterialIcon';

/**
 * oip-filter-chips
 * Renders a chip for each currently selected filter value.
 * Each chip shows the display label (registered by oip-filter-option) and a remove button.
 * Hidden when nothing is selected.
 */
const FilterChips: AC<{}> = () => {
  const { selected, isFiltered, optionLabels, toggle, clearAll } =
    useSignalTest();

  if (!isFiltered.value) return null;

  return (
    <div class="oip-filter-chips">
      {Object.entries(selected.value).map(([group, values]) =>
        values.map((value) => {
          const label = optionLabels[group]?.[value] ?? value;
          return (
            <div key={`${group}-${value}`} class="oip-filter-chip">
              <span class="oip-filter-chip__label">{label}</span>
              <button
                type="button"
                class="oip-filter-chip__remove"
                onClick={() => toggle(group, value)}
                aria-label={`Verwijder filter: ${label}`}
              >
                <MaterialIcon name="close" />
              </button>
            </div>
          );
        })
      )}
      <button
        type="button"
        class="oip-filter-chips__clear-button"
        onClick={clearAll}
      >
        Filters wissen
      </button>
    </div>
  );
};

export default FilterChips;
