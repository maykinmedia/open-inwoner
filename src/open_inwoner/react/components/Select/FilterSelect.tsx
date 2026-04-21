import { normalizeBoolean } from '@react/lib/attributes/attribute';
import { BooleanLike } from '@react/types/attributes';
import { type AnyComponent as AC } from 'preact';
import { SelectContext } from './context';
import { useFilterSelectProvider } from './useFilterSelectProvider';
import SelectView from './SelectView';
import { SelectProps } from './Select';

/**
 * oip-filter-select
 * Filter-aware variant of oip-select. Reads and writes selection state through
 * SignalTestContext when nested inside oip-sig-root-test. Falls back to own
 * signal state when used standalone (e.g. in Storybook).
 */
const FilterSelect: AC<SelectProps> = ({
  name,
  label,
  alwaysOpen: alwaysOpenProp = false,
  multiple: multipleProp = true,
  children,
}) => {
  const alwaysOpen = normalizeBoolean(alwaysOpenProp);
  const multiple = normalizeBoolean(multipleProp);

  const { containerRef, buttonRef, isOpen, toggleDropdown, ...ctx } =
    useFilterSelectProvider(name, multiple);

  return (
    <SelectContext.Provider value={ctx}>
      <SelectView
        name={name}
        label={label}
        alwaysOpen={alwaysOpen}
        multiple={multiple}
        containerRef={containerRef}
        buttonRef={buttonRef}
        isOpen={isOpen}
        selectedValues={ctx.selectedValues}
        toggleDropdown={toggleDropdown}
        close={ctx.close}
      >
        {children}
      </SelectView>
    </SelectContext.Provider>
  );
};

export default FilterSelect;
