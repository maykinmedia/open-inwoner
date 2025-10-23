import { getJsonFromScriptTag } from '@react/lib/getJsonScriptData'
import ReactDOM from 'react-dom/client'
import { ComboBoxItem, KVKBranchSelector } from './KVKBranchSelector'
import { getIntlProviderProps } from '@react/i18n/i18n'
import { ReactElement } from 'react'
import { IntlProvider } from 'react-intl'

class KVKBranchSelectorWebComponent extends HTMLElement {
  data: {
    items: ComboBoxItem[]
    selected_id?: string
  }
  constructor() {
    super()

    this.data = getJsonFromScriptTag<{
      items: ComboBoxItem[]
      selected_id?: string
    }>('branch-data')!
  }

  async connectedCallback() {
    // Extract branch data from embedded JSON script tag
    if (!this.data || !this.data.items || this.data.items.length === 0) {
      console.error(
        new Error('[KVKBranchSelectorModule] No branches available')
      )
      this.innerHTML = `<p class="utrecht-paragraph" style="color:var(--color-red-notification);">Er is een probleem opgetreden bij het laden van de vestigingen. Probeer de pagina te vernieuwen.</p>`
      return
    }

    const root = ReactDOM.createRoot(this)

    const data = this.data

    const intlProps = await getIntlProviderProps()

    console.log(intlProps)

    // nodes.items.forEach((el) => {
    try {
      const items = data.items
      const selectedId = data.selected_id

      // Read component configuration from data attributes
      const id = this.getAttribute('data-id') || 'select-combobox'
      const label =
        this.getAttribute('data-label') ||
        'Selecteer de rechtspersoon of vestiging waarmee u wilt inloggen'
      const name = this.getAttribute('data-name') || 'branch_number'

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
      )

      root.render(element)
    } catch (err) {
      console.error('[KVKBranchSelectorModule] Failed to mount:', err)
    }
  }
}

export default KVKBranchSelectorWebComponent
