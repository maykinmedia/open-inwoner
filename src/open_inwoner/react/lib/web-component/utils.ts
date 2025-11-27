import register from 'preact-custom-element';
import { AnyComponent } from 'preact';
import { wcRegistry as wcRegistry } from './registry';
import { WebComponentContext } from './types';
import { withIntl } from './plugins';

/**
 * Extended options for web component registration
 */
type RegisterOptions =
  | {
      shadow: false;
      /**
       * Whether to automatically wrap the component with IntlProvider for i18n support
       * @default false
       */
      i18n?: boolean;
    }
  | {
      shadow: true;
      mode?: 'open' | 'closed';
      adoptedStyleSheets?: CSSStyleSheet[];
      serializable?: boolean;
      /**
       * Whether to automatically wrap the component with IntlProvider for i18n support
       * @default false
       */
      i18n?: boolean;
    };

/**
 * Find all unique web component names on the current page
 * @returns a unique array of founded component names or null.
 */
export const findWebComponentsOnPage = (): string[] => {
  const selector = Object.keys(wcRegistry).join(',');
  const elements = document.querySelectorAll<HTMLElement>(selector);
  const foundComponents = [...elements].map((el) => el.tagName.toLowerCase());
  return Array.from(new Set(foundComponents));
};

/**
 * Create context objects for all elements of a specific component
 */
export const createContextsForComponent = (
  componentName: string
): WebComponentContext[] => {
  const elements = document.querySelectorAll<HTMLElement>(componentName);
  return [...elements].map((element) => ({ componentName, element }));
};

/**
 * Wrapper built around `register` to make sure that
 * there is a check if the web-component is already
 * declared, and to support additional options like i18n.
 *
 * @param Component - The Preact component to register
 * @param tagName - The custom element tag name
 * @param propNames - Array of prop names to expose as attributes
 * @param options - Extended registration options including i18n support
 */
export function registerWebComponent<P = {}, S = {}>(
  Component: AnyComponent<P, S>,
  tagName?: string,
  propNames?: (keyof P)[],
  options?: RegisterOptions
): HTMLElement {
  if (customElements.get(tagName ?? '')) return undefined!;

  // If i18n option is enabled, wrap the component with IntlProvider
  const ComponentToRegister = options?.i18n ? withIntl(Component) : Component;

  // Remove i18n from options before passing to preact-custom-element
  const { i18n, ...registerOptions } = options || {};

  return register(
    ComponentToRegister,
    tagName,
    propNames,
    registerOptions as any
  );
}
