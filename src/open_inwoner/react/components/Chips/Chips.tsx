import { type AnyComponent as AC } from 'preact';
import { Button } from '../Button';
import Chip from './Chip';
import { ChipsContext } from './context';
import { useChipsProvider } from './useChipsProvider';

/**
 * Renders a chip for each currently active filter value, plus a clear-all button.
 * Hidden when nothing is selected.
 *
 * Provides ChipsContext so sub-components can read shared state.
 * Bridges up to SignalTestContext automatically when present (web-component mode).
 */
const Chips: AC<{}> = () => {
  const ctx = useChipsProvider();
  const { selected, isFiltered, optionLabels, toggle, clearAll } = ctx;

  if (!isFiltered.value) return null;

  return (
    <ChipsContext.Provider value={ctx}>
      <div class="oip-filter-chips">
        {Object.entries(selected.value).map(([group, values]) =>
          values.map((value) => (
            <Chip
              key={`${group}-${value}`}
              group={group}
              value={value}
              label={optionLabels[group]?.[value] ?? value}
              toggle={toggle}
            />
          ))
        )}
        <Button
          className="oip-filter-chips__clear-button"
          handleClick={clearAll}
          variant="primary"
        >
          Filters wissen
        </Button>
      </div>
    </ChipsContext.Provider>
  );
};

export default Chips;
