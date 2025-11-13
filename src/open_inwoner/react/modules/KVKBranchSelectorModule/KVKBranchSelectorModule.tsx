import { ReactElement } from 'react';
import { createRoot, Root } from 'react-dom/client';
import { IntlProvider } from 'react-intl';
import { KVKBranchSelector } from '@react/components/KVKBranchSelector';
import { getIntlProviderProps } from '@react/i18n/i18n';
import { getJsonFromScriptTag } from '@react/lib/getJsonScriptData';

export interface ComboBoxItem {
  id: string;
  label: string;
  subLabel?: string;
  vestigingsnummer?: string;
  type?: string;
}

/**
 * Module for mounting KVKBranchSelector React components into Django templates.
 * Searches for elements with data-react-module="kvkbranchselector" and initializes them.
 */
export default class KVKBranchSelectorModule {
  /**
   * Creates a React element from current DOM state (for module Story)
   */
  static get root() {
    // Read from DOM
    const data = getJsonFromScriptTag<{
      items: ComboBoxItem[];
      selected_id?: string;
    }>('branch-data');

    const rootElement = document.getElementById('react-kvkbranchselector');
    const id = rootElement?.getAttribute('data-id') || 'select-combobox';
    const label =
      rootElement?.getAttribute('data-label') ||
      'Selecteer de rechtspersoon of vestiging waarmee u wilt inloggen';
    const name = rootElement?.getAttribute('data-name') || 'branch_number';

    // Handle error cases (empty data)
    if (!data || !data.items || data.items.length === 0) {
      return (
        <p
          className="utrecht-paragraph"
          style={{ color: 'var(--color-red-notification)' }}
        >
          Er is een probleem opgetreden bij het laden van de vestigingen.
        </p>
      );
    }

    // Return component
    return (
      <KVKBranchSelector
        id={id}
        label={label}
        name={name}
        branches={data.items}
        selectedBranchId={data.selected_id}
      />
    );
  }

  static async init(): Promise<void> {
    const intlProps = await getIntlProviderProps();
    const nodes = document.querySelectorAll<HTMLElement>(
      '[data-react-module="kvkbranchselector"]'
    );

    nodes.forEach((el) => {
      try {
        // Reuse existing React root if available to prevent remounting
        const rootKey = '_reactRoot';
        let root: Root | undefined = (el as any)[rootKey];

        // Extract branch data from embedded JSON script tag
        const data = getJsonFromScriptTag<{
          items: ComboBoxItem[];
          selected_id?: string;
        }>('branch-data');

        if (!data || !data.items || data.items.length === 0) {
          console.error(
            new Error('[KVKBranchSelectorModule] No branches available')
          );
          el.innerHTML = `<p class="utrecht-paragraph" style="color:var(--color-red-notification);">Er is een probleem opgetreden bij het laden van de vestigingen. Probeer de pagina te vernieuwen.</p>`;
          return;
        }

        const items = data.items;
        const selectedId = data.selected_id;

        // Read component configuration from data attributes
        const id = el.getAttribute('data-id') || 'select-combobox';
        const label =
          el.getAttribute('data-label') ||
          'Selecteer de rechtspersoon of vestiging waarmee u wilt inloggen';
        const name = el.getAttribute('data-name') || 'branch_number';

        // Create React root if it doesn't exist
        if (!root) {
          root = createRoot(el);
          (el as any)[rootKey] = root;
        }

        // Render component with i18n provider
        const element: ReactElement = (
          <IntlProvider {...intlProps}>
            <KVKBranchSelector
              id={id}
              label={label}
              name={name}
              branches={items}
              selectedBranchId={selectedId}
            />
          </IntlProvider>
        );

        root.render(element);
      } catch (err) {
        console.error('[KVKBranchSelectorModule] Failed to mount:', err);
        // TODO: Replace paragraph with NLDS component once available.
        el.innerHTML = `<p class="utrecht-paragraph" style="color:var(--color-red-notification);">We kunnen de vestigingen niet tonen vanwege een technische fout.</p>`;
      }
    });
  }
}
