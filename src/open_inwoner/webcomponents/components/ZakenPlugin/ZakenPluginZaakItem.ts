import { LitElement, html, unsafeCSS } from 'lit';
import { customElement, property } from 'lit/decorators.js';
// Styles from project, TODO: remove these project styles when switching to Preact and shadow DOM is off
import materialIcons from 'material-icons/iconfont/material-icons.css?inline';
import buttonStyles from '../../../scss/components/Button/Button.scss?inline';
// Styles for this component, TODO: keep these when switching to Preact
import componentStyles from './ZakenPluginZaakItem.scss?inline';

// Nore: For accessibility reasons Cards without meaningful content should not include an H2 heading

@customElement('oip-zaken-plugin-zaak-item')
export class ZakenPluginZaakItem extends LitElement {
  @property({ type: String })
  accessor description: string = '';

  @property({ type: String })
  accessor identificatie: string = '';

  @property({ type: String, attribute: 'detail-url' })
  accessor detailUrl: string = '';

  // Project styles and component style, TODO: move when switching to Preact and shadow DOM is off
  static styles = [
    unsafeCSS(materialIcons),
    unsafeCSS(buttonStyles),
    unsafeCSS(componentStyles),
  ];

  render() {
    return html`
      <article
        class="case-card"
        tabindex="0"
        role="main"
        aria-labelledby="zaak-${this.identificatie}"
      >
        <div class="case-card__content">
          <div class="case-card__heading">
            <p id="zaak-${this.identificatie}" class="utrecht-heading-2">
              <a href="${this.detailUrl}" class="case-card__link">
                ${this.description || this.identificatie}
              </a>
            </p>
          </div>

          <div class="case-card__body">
            <p class="utrecht-paragraph-muted">
              Zaaknummer: ${this.identificatie}
            </p>

            <p class="utrecht-paragraph">
              <a
                href="${this.detailUrl}"
                class="case-card__link"
                aria-label="Bekijk zaak ${this.identificatie}"
              >
                <span class="button button--icon-before button--transparent">
                  Bekijk zaak
                  <span class="material-icons-outlined" aria-hidden="true">
                    east
                  </span>
                </span>
              </a>
            </p>
          </div>
        </div>
      </article>
    `;
  }
}

export default ZakenPluginZaakItem;
