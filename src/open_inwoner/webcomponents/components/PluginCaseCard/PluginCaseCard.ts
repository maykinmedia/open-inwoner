import { LitElement, html, unsafeCSS } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import componentStyles from './PluginCaseCard.scss?inline';
import materialIcons from 'material-icons/iconfont/material-icons.css?inline';

interface Case {
  uuid: string;
  api_group_id: string;
  description?: string;
  case_type?: string;
  identification: string;
  url?: string; // Optional: if URL is pre-computed on backend
}

@customElement('case-cards')
class PluginCaseCards extends LitElement {
  @property({ type: Array })
  accessor cases: Case[] = [];

  @property({ type: String })
  accessor title: string = '';

  // Parse JSON from the "cases" attribute when component loads
  connectedCallback() {
    super.connectedCallback();
    const casesAttr = this.getAttribute('cases');
    if (casesAttr) {
      try {
        this.cases = JSON.parse(casesAttr);
      } catch (e) {
        console.error('Failed to parse cases JSON:', e);
        this.cases = [];
      }
    }

    const titleAttr = this.getAttribute('title');
    if (titleAttr) {
      this.title = titleAttr;
    }
  }

  // Combine Material Icons and component styles
  static styles = [unsafeCSS(materialIcons), unsafeCSS(componentStyles)];

  // Helper to build case URL (matches Django URL pattern)
  getCaseUrl(caseItem: Case): string {
    // If URL is pre-computed on backend
    if (caseItem.url) {
      return caseItem.url;
    }
    // Otherwise build it here (adjust path as needed)
    return `/cases/${caseItem.uuid}/${caseItem.api_group_id}/`;
  }

  render() {
    if (!this.cases || this.cases.length === 0) {
      return html``;
    }

    return html`
      <section class="plugin">
        ${this.title
          ? html`<h2 class="utrecht-heading-2">${this.title}</h2>`
          : ''}

        <div class="card-container card-container--columns-2 plugin-card">
          ${this.cases.map(
            (caseItem) => html`
              <a
                href="${this.getCaseUrl(caseItem)}"
                class="card card--status card--status--info"
              >
                <div class="card__body card__body--tabled">
                  <h3 class="utrecht-heading-3 case-card__title">
                    ${caseItem.description
                      ? html`<span class="status"
                          >${caseItem.description}</span
                        >`
                      : ''}
                    ${caseItem.case_type ? html` | ${caseItem.case_type}` : ''}
                  </h3>

                  <p class="case-card-card__description">
                    Zaaknummer
                    <span class="status">${caseItem.identification}</span>
                  </p>

                  <span class="button button--icon-before button--transparent">
                    Bekijk zaak
                    <span class="material-icons-outlined" aria-hidden="true"
                      >east</span
                    >
                  </span>
                </div>
              </a>
            `
          )}
        </div>
      </section>
    `;
  }
}

export default PluginCaseCards;
