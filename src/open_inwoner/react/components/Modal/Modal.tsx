import { MaterialIcon } from '@react/components/MaterialIcon';
import { Button } from '../Button';
import { FormattedMessage } from 'react-intl';
import { cloneElement, type AnyComponent as AC } from 'preact';
import { Children } from 'preact/compat';
import { ModalContext } from './context';
import { useModalProvider } from './useModalProvider';

export interface FilterModalProps {
  onClose: () => void;
}

/**
 * FilterModal — full-screen mobile modal containing the filter groups.
 *
 * Provides ModalContext so sub-components can read shared state.
 * Bridges up to SignalTestContext automatically when present (web-component mode).
 *
 * Children (Select components) receive alwaysOpen=true automatically.
 */
const FilterModal: AC<FilterModalProps> = ({ onClose, children }) => {
  const ctx = useModalProvider({ onClose });
  const { isDirty, close, apply, clear } = ctx;

  return (
    <ModalContext.Provider value={ctx}>
      <div
        class="oip-filter-modal__backdrop"
        onClick={(e) => {
          if (e.target === e.currentTarget) close();
        }}
      >
        <div class="oip-filter-modal">
          <header class="oip-filter-modal__header">
            <div class="oip-filter-modal__header-actions">
              <Button
                variant="primary"
                handleClick={close}
                transparent
                className="oip-filter-modal__close"
                title="Sluiten"
              >
                <MaterialIcon name="close" />
              </Button>
              <Button variant="primary" handleClick={clear} transparent>
                <span class="button__inner-text">
                  <FormattedMessage
                    id="filter.clear_all"
                    description="The label of the 'clear all' button."
                    defaultMessage="Wis alle filters"
                  />
                </span>
              </Button>
            </div>
            <h2 class="oip-filter-modal__heading">
              <FormattedMessage
                id="filter.mobile_title"
                description="The title of the mobile dialog filters"
                defaultMessage="Filters"
              />
            </h2>
          </header>
          <div class="oip-filter-modal__content">
            {Children.map(children, (child) =>
              cloneElement(child as any, { alwaysOpen: true })
            )}
          </div>
          <div class="oip-filter-modal__footer">
            <Button
              variant="primary"
              handleClick={apply}
              disabled={!isDirty.value}
              fullWidth
            >
              <span class="button__inner-text">
                <FormattedMessage
                  id="filter.show_results"
                  description="Show results text"
                  defaultMessage="Toon resultaten"
                />
              </span>
            </Button>
          </div>
        </div>
      </div>
    </ModalContext.Provider>
  );
};

export default FilterModal;
