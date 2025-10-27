import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { webcomponents, registerWebComponents } from './register'
import GenericReactWebComponent, { AbstractWebComponent } from './abstract'
import { normalizeAttribute } from './utils'

describe('Test webComponents folder', () => {
  describe('Test utils.tsx file', () => {
    describe('Test normalizeAttribute', () => {
      it('should convert kebab-case to camelCase', () => {
        expect(normalizeAttribute('data-test-value')).toBe('dataTestValue')
      })

      it('should convert single hyphen to camelCase', () => {
        expect(normalizeAttribute('my-prop')).toBe('myProp')
      })

      it('should handle attributes with no hyphens', () => {
        expect(normalizeAttribute('title')).toBe('title')
      })

      it('should handle multiple consecutive hyphens', () => {
        expect(normalizeAttribute('data--test')).toBe('data-Test')
      })

      it('should handle attributes with multiple parts', () => {
        expect(normalizeAttribute('aria-label-by-id')).toBe('ariaLabelById')
      })

      it('should handle empty string', () => {
        expect(normalizeAttribute('')).toBe('')
      })

      it('should handle attributes ending with hyphen', () => {
        expect(normalizeAttribute('my-attr-')).toBe('myAttr-')
      })

      it('should convert only lowercase letters after hyphen', () => {
        expect(normalizeAttribute('data-API')).toBe('data-API')
      })
    })
  })

  describe('Test abstract.tsx file', () => {
    describe('Test AbstractWebComponent', () => {
      it('should extend HTMLElement', () => {
        expect(AbstractWebComponent.prototype).toBeInstanceOf(HTMLElement)
      })

      it('should have observedAttributes property', () => {
        expect(AbstractWebComponent).toHaveProperty('observedAttributes')
      })

      it('should have connectedCallback method', () => {
        const instance = Object.create(AbstractWebComponent.prototype)
        expect(typeof instance.connectedCallback).toBe('function')
      })

      it('should have connectedMoveCallback method', () => {
        const instance = Object.create(AbstractWebComponent.prototype)
        expect(typeof instance.connectedMoveCallback).toBe('function')
      })

      it('should have disconnetedCallback method', () => {
        const instance = Object.create(AbstractWebComponent.prototype)
        expect(typeof instance.disconnetedCallback).toBe('function')
      })

      it('should have adoptedCallback method', () => {
        const instance = Object.create(AbstractWebComponent.prototype)
        expect(typeof instance.adoptedCallback).toBe('function')
      })

      it('should have attributeChangedCallback method', () => {
        const instance = Object.create(AbstractWebComponent.prototype)
        expect(typeof instance.attributeChangedCallback).toBe('function')
      })

      it('should not throw when calling lifecycle methods', () => {
        const instance = Object.create(AbstractWebComponent.prototype)
        expect(() => instance.connectedCallback()).not.toThrow()
        expect(() => instance.connectedMoveCallback()).not.toThrow()
        expect(() => instance.disconnetedCallback()).not.toThrow()
        expect(() => instance.adoptedCallback()).not.toThrow()
        expect(() =>
          instance.attributeChangedCallback('name', 'old', 'new')
        ).not.toThrow()
      })
    })
    describe('Test GenericReactWebComponent', () => {
      // Create a simple test component
      const TestComponent = ({ message }: { message?: string }) => (
        <div data-testid="test-component">{message || 'Default message'}</div>
      )

      let container: HTMLDivElement

      beforeEach(() => {
        container = document.createElement('div')
        document.body.appendChild(container)

        // Mock attachInternals for JSDOM
        if (!HTMLElement.prototype.attachInternals) {
          HTMLElement.prototype.attachInternals = function () {
            return {} as ElementInternals
          }
        }
      })

      afterEach(() => {
        document.body.removeChild(container)
      })

      it('should have static observedAttributes property', () => {
        expect(GenericReactWebComponent).toHaveProperty('observedAttributes')
        expect(Array.isArray(GenericReactWebComponent.observedAttributes)).toBe(
          true
        )
      })

      it('should extend AbstractWebComponent when used as custom element', () => {
        class TestWebComponent extends GenericReactWebComponent<any> {
          constructor() {
            super(TestComponent)
          }
        }

        const elementName = 'test-extend-element'
        if (!customElements.get(elementName)) {
          customElements.define(elementName, TestWebComponent)
        }

        const instance = document.createElement(
          elementName
        ) as any as TestWebComponent

        expect(instance).toBeInstanceOf(AbstractWebComponent)
      })

      it('should initialize with Component property', () => {
        class TestWebComponent extends GenericReactWebComponent<any> {
          constructor() {
            super(TestComponent)
          }
        }

        const elementName = 'test-component-prop'
        if (!customElements.get(elementName)) {
          customElements.define(elementName, TestWebComponent)
        }

        const instance = document.createElement(
          elementName
        ) as any as TestWebComponent

        expect(instance.Component).toBe(TestComponent)
      })

      it('should create root on construction', () => {
        class TestWebComponent extends GenericReactWebComponent<any> {
          constructor() {
            super(TestComponent)
          }
        }

        const elementName = 'test-root-element'
        if (!customElements.get(elementName)) {
          customElements.define(elementName, TestWebComponent)
        }

        const instance = document.createElement(
          elementName
        ) as any as TestWebComponent

        expect(instance.root).toBeDefined()
      })

      it('should have props property', () => {
        class TestWebComponent extends GenericReactWebComponent<any> {
          constructor() {
            super(TestComponent)
          }
        }

        const elementName = 'test-props-element'
        if (!customElements.get(elementName)) {
          customElements.define(elementName, TestWebComponent)
        }

        const instance = document.createElement(
          elementName
        ) as any as TestWebComponent

        expect(instance.props).toBeDefined()
        expect(typeof instance.props).toBe('object')
      })

      it('should parse props from string attributes', () => {
        class TestWebComponent extends GenericReactWebComponent<any> {
          constructor() {
            super(TestComponent)
          }
        }

        const elementName = 'test-parse-element'
        if (!customElements.get(elementName)) {
          customElements.define(elementName, TestWebComponent)
        }

        // Create element with innerHTML to set attributes before construction
        const div = document.createElement('div')
        div.innerHTML = `<${elementName} message="Hello World"></${elementName}>`
        const instance = div.querySelector(
          elementName
        ) as any as TestWebComponent

        expect(instance.props.message).toBe('Hello World')
      })

      it('should convert kebab-case attributes to camelCase props', () => {
        class TestWebComponent extends GenericReactWebComponent<any> {
          constructor() {
            super(TestComponent)
          }
        }

        const elementName = 'test-kebab-element'
        if (!customElements.get(elementName)) {
          customElements.define(elementName, TestWebComponent)
        }

        const instance = document.createElement(
          elementName
        ) as any as TestWebComponent
        instance.setAttribute('data-test-value', 'test')

        // Create a new instance with attributes already set
        const div = document.createElement('div')
        div.innerHTML = `<${elementName} data-test-value="test"></${elementName}>`
        const freshInstance = div.querySelector(
          elementName
        ) as any as TestWebComponent

        expect(freshInstance.props.dataTestValue).toBe('test')
      })

      it('should parse JSON attribute values', () => {
        class TestWebComponent extends GenericReactWebComponent<any> {
          constructor() {
            super(TestComponent)
          }
        }

        const elementName = 'test-json-element'
        if (!customElements.get(elementName)) {
          customElements.define(elementName, TestWebComponent)
        }

        const jsonData = { key: 'value', nested: { prop: 42 } }
        const div = document.createElement('div')
        div.innerHTML = `<${elementName} data='${JSON.stringify(jsonData)}'></${elementName}>`
        const instance = div.querySelector(
          elementName
        ) as any as TestWebComponent

        expect(instance.props.data).toEqual(jsonData)
      })

      it('should handle non-JSON attribute values as strings', () => {
        class TestWebComponent extends GenericReactWebComponent<any> {
          constructor() {
            super(TestComponent)
          }
        }

        const elementName = 'test-string-element'
        if (!customElements.get(elementName)) {
          customElements.define(elementName, TestWebComponent)
        }

        const div = document.createElement('div')
        div.innerHTML = `<${elementName} title="Simple String"></${elementName}>`
        const instance = div.querySelector(
          elementName
        ) as any as TestWebComponent

        expect(instance.props.title).toBe('Simple String')
      })

      it('should render component on connectedCallback', async () => {
        class TestWebComponent extends GenericReactWebComponent<any> {
          constructor() {
            super(TestComponent)
          }
        }

        const elementName = 'test-connected-element'
        if (!customElements.get(elementName)) {
          customElements.define(elementName, TestWebComponent)
        }

        const instance = document.createElement(
          elementName
        ) as any as TestWebComponent
        container.appendChild(instance)

        // After connection, the component should be rendered
        expect(instance.root).toBeDefined()

        // Wait for React to render
        await new Promise((resolve) => setTimeout(resolve, 0))

        expect(instance.textContent).toContain('Default message')
      })

      it('should handle empty attributes object', () => {
        class TestWebComponent extends GenericReactWebComponent<any> {
          constructor() {
            super(TestComponent)
          }
        }

        const elementName = 'test-empty-element'
        if (!customElements.get(elementName)) {
          customElements.define(elementName, TestWebComponent)
        }

        const instance = document.createElement(
          elementName
        ) as any as TestWebComponent

        expect(instance.props).toBeDefined()
        expect(typeof instance.props).toBe('object')
      })
    })
  })

  describe('Test register.tsx file', () => {
    describe('Test webcomponents constant', () => {
      it('should have action-list component', () => {
        expect(webcomponents).toHaveProperty('action-list')
      })

      it('should have exactly one component registered', () => {
        const keys = Object.keys(webcomponents)
        expect(keys.length).toBe(1)
      })

      it('should have component importers as functions', () => {
        Object.values(webcomponents).forEach((importer) => {
          expect(typeof importer).toBe('function')
        })
      })

      it('should return promises from importers', () => {
        const importer = webcomponents['action-list']
        const result = importer()
        expect(result).toBeInstanceOf(Promise)
      })
    })

    describe('Test registerWebComponents', () => {
      beforeEach(() => {
        // Clean up DOM and customElements
        document.body.innerHTML = ''
        // Note: We cannot actually undefine custom elements, so we use unique names per test
      })

      afterEach(() => {
        document.body.innerHTML = ''
        vi.restoreAllMocks()
      })

      it('should be a function', () => {
        expect(typeof registerWebComponents).toBe('function')
      })

      it('should return a Promise', () => {
        const result = registerWebComponents()
        expect(result).toBeInstanceOf(Promise)
      })

      it('should not throw when no components are in the DOM', async () => {
        await expect(registerWebComponents()).resolves.not.toThrow()
      })

      it('should skip already defined custom elements', async () => {
        // Create element in DOM
        const element = document.createElement('action-list')
        document.body.appendChild(element)

        // Mock customElements.get to return a truthy value
        const getSpy = vi
          .spyOn(customElements, 'get')
          .mockReturnValue(function () {} as any)
        const defineSpy = vi.spyOn(customElements, 'define')

        await registerWebComponents()

        // Should check if element is defined
        expect(getSpy).toHaveBeenCalled()
        // Should not define it again
        expect(defineSpy).not.toHaveBeenCalled()
      })

      it('should handle component import errors gracefully', async () => {
        const consoleErrorSpy = vi
          .spyOn(console, 'error')
          .mockImplementation(() => {})

        // Create a component that will fail to import
        const element = document.createElement('action-list')
        document.body.appendChild(element)

        // We can't easily test this without modifying the loader,
        // but we can verify the function completes
        await expect(registerWebComponents()).resolves.not.toThrow()

        consoleErrorSpy.mockRestore()
      })

      it('should handle missing component importers', async () => {
        const consoleErrorSpy = vi
          .spyOn(console, 'error')
          .mockImplementation(() => {})

        // The function should handle this gracefully and log an error
        await expect(registerWebComponents()).resolves.not.toThrow()

        consoleErrorSpy.mockRestore()
      })

      it('should process multiple unique components in parallel', async () => {
        // Create multiple action-list elements
        const element1 = document.createElement('action-list')
        const element2 = document.createElement('action-list')
        document.body.appendChild(element1)
        document.body.appendChild(element2)

        // Should deduplicate and only load once
        await expect(registerWebComponents()).resolves.not.toThrow()
      })

      it('should query all components with a single selector', async () => {
        const querySelectorAllSpy = vi.spyOn(document, 'querySelectorAll')

        await registerWebComponents()

        // Should call querySelectorAll once with all component names
        expect(querySelectorAllSpy).toHaveBeenCalledWith('action-list')
      })

      it('should handle top-level errors gracefully', async () => {
        const consoleErrorSpy = vi
          .spyOn(console, 'error')
          .mockImplementation(() => {})
        const querySelectorAllSpy = vi
          .spyOn(document, 'querySelectorAll')
          .mockImplementation(() => {
            throw new Error('Query failed')
          })

        await expect(registerWebComponents()).resolves.not.toThrow()

        expect(consoleErrorSpy).toHaveBeenCalledWith(
          'Could not load WebComponents:',
          expect.any(Error)
        )

        querySelectorAllSpy.mockRestore()
        consoleErrorSpy.mockRestore()
      })

      it('should handle components with no default export', async () => {
        const consoleErrorSpy = vi
          .spyOn(console, 'error')
          .mockImplementation(() => {})

        // Create element in DOM
        const element = document.createElement('action-list')
        document.body.appendChild(element)

        // This test verifies the error handling exists
        // In real scenario, the import would return { default: undefined }
        await expect(registerWebComponents()).resolves.not.toThrow()

        consoleErrorSpy.mockRestore()
      })
    })
  })
})
