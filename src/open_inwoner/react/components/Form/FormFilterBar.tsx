import { type AnyComponent as AC } from 'preact';
import { FormattedMessage } from 'react-intl';

/**
 * oip-filter-bar
 * Horizontal bar that lays out oip-select fields and an oip-form-button.
 * Pure layout component — no form logic.
 */
const FormFilterBar: AC<{}> = ({ children }) => (
  <div class="oip-filter-bar oip-filter-bar--desktop">
    <span class="oip-filter-bar__label">
      <FormattedMessage
        id="filter.heading"
        description="The title of the filters"
        defaultMessage="Filter op:"
      />
    </span>
    {children}
  </div>
);

export default FormFilterBar;
