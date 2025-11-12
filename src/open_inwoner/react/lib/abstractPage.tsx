import { getIntlProviderProps } from '@react/i18n/i18n';
import { JSX } from 'react';
import { Root, createRoot } from 'react-dom/client';
import { IntlConfig, IntlProvider } from 'react-intl';

export abstract class AbstractPage {
  static reactRoot: Root;
  static rootNode: Element;
  static root: JSX.Element;

  static async init() {
    try {
      const intlProviderProps = await getIntlProviderProps();
      this.initPage(intlProviderProps);
    } catch (err) {
      console.log(err);
    }
  }

  static async initPage(intlProps: IntlConfig) {
    // find root node for our root component
    if (!this.rootNode) throw new Error('No reactNode defined');
    this.reactRoot = createRoot(this.rootNode);

    if (!this.root) throw new Error('No root defined');
    this.reactRoot.render(
      <IntlProvider {...intlProps}>{this.root}</IntlProvider>
    );
  }
}
