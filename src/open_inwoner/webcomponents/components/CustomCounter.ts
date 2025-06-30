import { LitElement, html, css } from 'lit'
import { customElement, property } from 'lit/decorators.js'

/**
 * Custom Counter Web Component using Lit
 * Example component with state management and data binding
 */
@customElement('custom-counter')
class CustomCounter extends LitElement {
  @property({ type: Number })
  // TODO: Update Prettier so it understands accessor keyword
  // TODO: Replace 'declare' with 'accessor'
  declare value: number

  @property({ type: Number })
  declare min: number

  @property({ type: Number })
  declare max: number

  @property({ type: Number })
  declare step: number

  @property({ type: Boolean })
  declare displayOnly: boolean

  static styles = css`
    :host {
      display: inline-block;
    }

    .counter-container {
      display: flex;
      align-items: center;
      border: 1px solid #ccc;
      border-radius: 4px;
      overflow: hidden;
      width: fit-content;
    }

    .counter-button {
      padding: 8px 12px;
      border: none;
      background: #f8f9fa;
      cursor: pointer;
      font-size: 16px;
      font-weight: bold;
    }

    .counter-button:hover:not(:disabled) {
      background: #e9ecef;
    }

    .counter-button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .counter-input {
      border: none;
      text-align: center;
      width: 60px;
      padding: 8px;
      font-size: 16px;
    }

    .counter-input:focus {
      outline: 2px solid #007bff;
      outline-offset: -2px;
    }

    .counter-info {
      margin-top: 8px;
      font-size: 12px;
      color: #666;
      text-align: center;
    }
  `

  constructor() {
    super()
    this.min = 0
    this.max = 100
    this.step = 1
    this.value = 0
    this.displayOnly = false
  }

  setValue(newValue: number) {
    const numValue = parseInt(newValue.toString()) || 0
    this.value = Math.max(this.min, Math.min(this.max, numValue))
  }

  increment() {
    this.setValue(this.value + this.step)
  }

  decrement() {
    this.setValue(this.value - this.step)
  }

  handleInput = (e: InputEvent) => {
    const target = e.target as HTMLInputElement
    this.setValue(parseInt(target?.value) || 0)
  }

  render() {
    const isDecrementDisabled = this.value <= this.min
    const isIncrementDisabled = this.value >= this.max

    return html`
      <div class="counter-container" part="container">
        <button
          class="counter-button"
          part="decrement-button"
          aria-label="Decrease value"
          ?disabled=${isDecrementDisabled}
          @click=${this.decrement}
        >
          −
        </button>
        <input
          class="counter-input"
          part="input"
          type="${this.displayOnly ? 'hidden' : 'number'}"
          min=${this.min}
          max=${this.max}
          .value=${this.value.toString()}
          @input=${this.handleInput}
        />
        <span
          class="counter-display"
          part="display"
          ?hidden=${!this.displayOnly}
          >${this.value}</span
        >
        <button
          class="counter-button"
          part="increment-button"
          aria-label="Increase value"
          ?disabled=${isIncrementDisabled}
          @click=${this.increment}
        >
          +
        </button>
      </div>
      <div class="counter-info" part="info">
        Range: ${this.min} - ${this.max}, Step: ${this.step}
      </div>
    `
  }
}

export default CustomCounter
