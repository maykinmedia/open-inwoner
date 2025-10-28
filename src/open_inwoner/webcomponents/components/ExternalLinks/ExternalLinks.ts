import { LitElement, html, unsafeCSS } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import componentStyles from './ExternalLinks.scss?inline';
import materialIcons from 'material-icons/iconfont/material-icons.css?inline';

interface ExternalLink {
  url: string;
  name: string;
  icon: string;
  target?: string;
}

@customElement('external-links')
class ExternalLinks extends LitElement {
  @property({ type: Array })
  accessor links: ExternalLink[] = [];

  @property({ type: String })
  accessor title: string = '';

  // Parse JSON from the "links" attribute when component loads
  connectedCallback() {
    super.connectedCallback();

    const linksAttr = this.getAttribute('links');
    if (linksAttr) {
      try {
        this.links = JSON.parse(linksAttr);
      } catch (e) {
        console.error('Failed to parse links JSON:', e);
        this.links = [];
      }
    }

    const titleAttr = this.getAttribute('title');
    if (titleAttr) {
      this.title = titleAttr;
    }
  }

  // Combine Material Icons and component styles
  static styles = [unsafeCSS(materialIcons), unsafeCSS(componentStyles)];

  // Helper to generate accessible aria-label
  getAriaLabel(link: ExternalLink): string {
    if (link.target === '_blank') {
      return `${link.name} (opens in new window)`;
    }
    return link.name;
  }

  render() {
    if (!this.links || this.links.length === 0) {
      return html``;
    }

    return html`
      <section class="plugin external-links">
        ${this.title
          ? html`<h2 class="utrecht-heading-2">${this.title}</h2>`
          : ''}

        <ul
          class="card-container card-container--columns-2 external-links__list"
        >
          ${this.links.map(
            (link) => html`
              <li class="external-links__list-item">
                <a
                  href="${link.url}"
                  class="external-link"
                  target="${link.target || '_self'}"
                  rel="${link.target === '_blank' ? 'noopener noreferrer' : ''}"
                  aria-label="${this.getAriaLabel(link)}"
                >
                  <span class="external-link__custom-icon">
                    <span class="material-icons-outlined" aria-hidden="true">
                      ${link.icon}
                    </span>
                  </span>
                  <span class="external-link__content">
                    <p>${link.name}</p>
                  </span>
                  <span class="external-link__arrow">
                    <span class="material-icons-outlined" aria-hidden="true"
                      >east</span
                    >
                  </span>
                </a>
              </li>
            `
          )}
        </ul>
      </section>
    `;
  }
}

export default ExternalLinks;
