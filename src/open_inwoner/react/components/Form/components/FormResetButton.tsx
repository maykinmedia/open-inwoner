import { withContextGuard } from '@react/lib/hooks/withContextGuard';
import { useFormContext, useRequiredFormContext } from '../context';
import { Button } from '../../Button';

/**
 * oip-form-reset-button
 *
 * Reset button bound to the nearest oip-form context.
 * Clears all field selections when clicked.
 *
 * Must be rendered inside oip-form (FormContext).
 */
const FormResetButton = withContextGuard(useFormContext, ({ children }) => {
  const formCtx = useRequiredFormContext();

  return (
    <Button
      type="button"
      className="oip-form-reset-button"
      handleClick={formCtx.reset}
      variant="secondary"
      transparent
    >
      {children || 'Reset formulier'}
    </Button>
  );
});

export default FormResetButton;
