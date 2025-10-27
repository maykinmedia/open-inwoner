import { parseJsonSafely } from '@react/lib/getJsonScriptData'
import { createRoot, Root } from 'react-dom/client'
import { FC } from 'react'
import { normalizeAttribute } from './utils'

export abstract class AbstractWebComponent extends HTMLElement {
  static observedAttributes: string[]
  connectedCallback() {}
  connectedMoveCallback() {}
  disconnetedCallback() {}
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
    const props: Record<string, T | string> = {}
    for (let index = 0; index < this.attributes.length; index++) {
      const attribute = this.attributes[index]
      const attr = normalizeAttribute(attribute.name)
      const value = attribute.value
      try {
        props[attr] = parseJsonSafely<T>(value) ?? value
      } catch {
        props[attr] = value
      }
    }
    return props as T
  }
}

export default GenericReactWebComponent
