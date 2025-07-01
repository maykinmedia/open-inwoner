import { Root, createRoot } from 'react-dom/client'
import { IntlConfig, IntlProvider } from 'react-intl'
import { getIntlProviderProps } from '@/i18n/i18n'
import Demo from './Demo'

export default class Page {
  static reactRoot: Root

  static async init() {
    try {
      const intlProviderProps = await getIntlProviderProps()
      this.initPage(intlProviderProps)
    } catch (err) {
      console.log(err)
    }
  }

  static async initPage(intlProps: IntlConfig) {
    // find root node for our root component
    const rootNode = document.querySelector('#react-root-demo')!

    this.reactRoot = createRoot(rootNode)

    this.reactRoot.render(
      <IntlProvider {...intlProps}>
        <Demo countNode={this.countNode} counterNode={this.counterNode} />
      </IntlProvider>
    )
  }

  static get countNode(): HTMLDivElement | null {
    return document.querySelector('#react-root-demo-count')
  }
  static get counterNode(): HTMLDivElement | null {
    return document.querySelector('#react-root-demo-counter')
  }
}
