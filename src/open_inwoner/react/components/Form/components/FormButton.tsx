import { withContextGuard } from '@react/lib/hooks/withContextGuard';
import {
  useFilterContext,
  useRequiredFilterContext,
} from '../../Filters/context';
import { useRequiredFormContext } from '../context';
import { Button } from '../../Button';
import { AnyComponent } from 'preact';

/**
 * oip-form-button
 *
 * Submit button bound to the nearest oip-form and oip-filters contexts.
 *
 * The button is disabled while the form selection has not changed from its
 * initial (page-load) state, preventing redundant submissions. When clicked
 * it delegates to `filterCtx.submit()`, which serialises current values into
 * URL query params and navigates.
 *
 * Must be rendered inside both oip-form (FormContext) and oip-filters (FilterContext).
 */
const FormButton: AnyComponent = ({ children }) => {
  const formCtx = useRequiredFormContext();
  const filterCtx = useRequiredFilterContext();

  return (
    <Button
      type="button"
      className="oip-form-button"
      disabled={!formCtx.isDirty.value}
      handleClick={filterCtx.submit} // not good yet.
      variant="primary"
    >
      {children || 'Toon resultaten'}
    </Button>
  );
};

FormButton.displayName = 'FormButton';

export default withContextGuard(useFilterContext, FormButton);
