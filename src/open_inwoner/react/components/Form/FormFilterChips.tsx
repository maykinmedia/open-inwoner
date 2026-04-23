import { type AnyComponent as AC } from 'preact';
import { useRequiredFormContext } from './FormContext';
import { Button } from '../Button';
import { FormattedMessage } from 'react-intl';

/**
 * oip-filter-chips
 * Reads all selected values from the nearest oip-form and renders a chip for
 * each one. Uses labels registered by oip-select options; falls back to the
 * raw value if no label was registered. Hidden when nothing is selected.
 */
const FormFilterChips: AC = () => {
  const formContext = useRequiredFormContext();

  if (formContext.isEmpty.value) return null;

  return (
    <div class="oip-filter-chips">
      {Object.entries(formContext.values.value).map(([fieldName, values]) =>
        values.map((value) => {
          const label = formContext.getLabel(fieldName, value);
          return (
            <div key={`${fieldName}-${value}`} class="oip-filter-chip">
              <span class="oip-filter-chip__label">{label}</span>
              <button
                type="button"
                class="oip-filter-chip__remove"
                onClick={() => formContext.removeValue(fieldName, value)}
                aria-label={`Verwijder filter: ${label}`}
              >
                ×
              </button>
            </div>
          );
        })
      )}
      <Button
        type="button"
        class="oip-filter-chips__clear"
        handleClick={formContext.reset}
        variant="secondary"
      >
        <FormattedMessage
          id="filter.reset"
          description="The text on the reset form button"
          defaultMessage="Filters wissen"
        />
      </Button>
    </div>
  );
};

export default FormFilterChips;
