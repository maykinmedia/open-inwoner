import { type AnyComponent as AC } from 'preact';
import { useRequiredFormContext } from './FormContext';
import { Button } from '../Button';

/**
 * oip-form-button
 * Submit button bound to the nearest oip-form context.
 * Disabled when the form selection has not changed from its initial state.
 */
const FormButton: AC = ({ children }) => {
  const formContext = useRequiredFormContext();

  return (
    <Button
      type="button"
      class="oip-form-button"
      disabled={!formContext.isDirty.value}
      handleClick={formContext.submit}
      variant="primary"
    >
      {children || 'Toon resultaten'}
    </Button>
  );
};

export default FormButton;
