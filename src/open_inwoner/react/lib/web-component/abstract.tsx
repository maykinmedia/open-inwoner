import { createRoot, Root } from 'react-dom/client'
import { FC } from 'react'
import { normalizeAttribute } from './utils'
import unescape from 'lodash.unescape'

export abstract class AbstractWebComponent extends HTMLElement {
  static observedAttributes: string[]
  connectedCallback() {}
  disconnectedCallback() {}
  adoptedCallback() {}
  attributeChangedCallback(
    _name: string,
    _oldValue: string,
    _newValue: string
  ) {}
}

class GenericReactWebComponent<T extends object> extends AbstractWebComponent {
  props: T
  _internals: ElementInternals
  root: Root
  Component: FC<T>
  static observedAttributes: string[] = []

  constructor(Component: FC<T>) {
    super()
    this._internals = this.attachInternals()
    this.props = this.getPropsFromAttributes()
    this.root = createRoot(this)
    this.Component = Component
  }

  connectedCallback(): void {
    const Component = this.Component
    this.root.render(<Component {...this.props} />)
  }

  private getPropsFromAttributes<T>(): T {
    const props: Record<string, unknown> = {}

    for (let i = 0; i < this.attributes.length; i++) {
      const attribute = this.attributes[i]
      const attr = normalizeAttribute(attribute.name)
      const value = unescape(attribute.value)

      try {
        // Try parsing as JSON
        props[attr] = JSON.parse(value)
      } catch {
        // Fallback to string
        props[attr] = value
      }
    }

    return props as T
  }
}

export default GenericReactWebComponent
