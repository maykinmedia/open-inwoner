import { LitElement, html, unsafeCSS } from 'lit';
import { customElement, property } from 'lit/decorators.js';
// Styles from project, TODO: remove these project styles when switching to Preact and shadow DOM is off
import materialIcons from 'material-icons/iconfont/material-icons.css?inline';
import appStyles from '../../../scss/views/App.scss?inline';
import spinnerStyles from '../../../scss/components/Spinner/Spinner.scss?inline';

@customElement('oip-loading-spinner')
export class LoadingSpinner extends LitElement {
  @property({ type: String, attribute: 'loading-text' })
  accessor loadingText: string = 'Laden...';

  @property({ type: String, attribute: 'icon-name' })
  accessor iconName: string = 'rotate_right';

  // Project styles and component style, TODO: move when switching to Preact and shadow DOM is off
  static styles = [
    unsafeCSS(materialIcons),
    unsafeCSS(spinnerStyles),
    unsafeCSS(appStyles),
  ];

  render() {
    return html`
      <div class="loader-container">
        <div class="spinner">
          <span class="material-icons spinner-icon rotate" aria-hidden="true">
            ${this.iconName}
          </span>
          <div class="spinner__content" role="status">${this.loadingText}</div>
        </div>
      </div>
    `;
  }
}

export default LoadingSpinner;
