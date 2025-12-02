import { LitElement, html, unsafeCSS } from 'lit';
import { customElement } from 'lit/decorators.js';
// Styles for this component, TODO: keep when switching to Preact
import componentStyles from './ZakenPluginContainer.scss?inline';

@customElement('oip-zaken-plugin-container')
export class ZakenPluginContainer extends LitElement {
  static styles = unsafeCSS(componentStyles);

  render() {
    return html`
      <div class="zaken-plugin-container">
        <slot name="error"></slot>
        <div class="case-cards case-cards__list">
          <slot></slot>
        </div>
      </div>
    `;
  }
}

export default ZakenPluginContainer;
