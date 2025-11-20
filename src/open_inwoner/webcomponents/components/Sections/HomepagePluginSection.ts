import { LitElement, html, unsafeCSS } from 'lit';
import { customElement, property } from 'lit/decorators.js';
// Styles from project, TODO: remove these project styles when switching to Preact and shadow DOM is off
import materialIcons from 'material-icons/iconfont/material-icons.css?inline';
import appStyles from '../../../scss/views/App.scss?inline';
import NLDSStyles from '@open-inwoner/design-tokens/dist/css/index.css?inline';
// Styles for this component, TODO: keep these when switching to Preact
import componentStyles from './HomepagePluginSection.scss?inline';

@customElement('oip-homepage-plugin-section')
export class HomepagePluginSection extends LitElement {
  @property({ type: String })
  accessor title: string = '';

  @property({ type: String, attribute: 'next-url' })
  accessor nextUrl: string = '';

  @property({ type: String, attribute: 'next-url-label' })
  accessor nextUrlLabel: string = '';

  // Show notifications icon - usage in HTML example:
  // {% if userfeed.action_required %}show-indicator="true"{% endif %}
  // Using converter to properly handle boolean attribute
  @property({
    type: Boolean,
    attribute: 'show-indicator',
    converter: {
      fromAttribute: (value) => value !== null && value !== 'false',
    },
  })
  accessor showIndicator: boolean = false;

  static styles = [
    unsafeCSS(materialIcons),
    unsafeCSS(componentStyles),
    unsafeCSS(appStyles),
    unsafeCSS(NLDSStyles),
  ];

  render() {
    return html`
      <section class="plugin">
        <header class="plugin__header">
          ${this.title
            ? html`
                <div
                  class="${this.showIndicator ? 'heading-2__indicator' : ''}"
                >
                  <h2
                    class="utrecht-heading-2 ${this.showIndicator
                      ? 'indicator'
                      : ''}"
                  >
                    ${this.title}
                  </h2>
                  ${this.showIndicator
                    ? html`
                        <span
                          aria-hidden="true"
                          class="material-icons plugin__notification-indicator"
                        >
                          fiber_manual_record
                        </span>
                      `
                    : ''}
                </div>
              `
            : ''}
          ${this.nextUrl
            ? html`
                <a
                  class="button button--textless button--icon button--icon-after"
                  href="${this.nextUrl}"
                  title="${this.nextUrlLabel}"
                  aria-label="${this.nextUrlLabel}"
                >
                  <span aria-hidden="true" class="material-icons">
                    arrow_forward
                  </span>
                  ${this.nextUrlLabel}
                </a>
              `
            : ''}
        </header>
        <slot></slot>
      </section>
    `;
  }
}

export default HomepagePluginSection;
