import { LitElement, html, css } from 'lit'
import { customElement, property } from 'lit/decorators.js'

/**
 * Custom Button Web Component using Lit
 * Example of a custom web component with styling and interactions
 */
@customElement('custom-button')
class CustomButton extends LitElement {
  @property({ type: String })
  // TODO: Update Prettier so it understands accessor keyword
  // TODO: Replace 'declare' with 'accessor'
  declare variant: string

  @property({ type: String })
  declare size: string

  @property({ type: Boolean })
  declare disabled: boolean

  @property({ type: Number })
  declare clickCount: number

  static styles = css`
    :host {
      display: inline-block;
    }

    button {
      all: unset;
      padding: 8px 16px;
      border: none;
      border-radius: 4px;
      background: #007bff;
      color: white;
      cursor: pointer;
      font-family: inherit;
      margin-top: 12px;
    }

    button:hover:not(:disabled) {
      background: #0056b3;
    }

    button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .click-count {
      margin-left: 8px;
    }
  `

  constructor() {
    super()
    this.variant = 'primary'
    this.size = 'medium'
    this.disabled = false
    this.clickCount = 0
  }

  increment() {
    this.clickCount = this.clickCount + 1
  }

  render() {
    return html`
      <button part="button" ?disabled=${this.disabled} @click=${this.increment}>
        <slot name="text"></slot>
        <slot name="icon"></slot>
      </button>
      <span class="click-count">Clicked: ${this.clickCount}</span>
    `
  }
}

export default CustomButton
