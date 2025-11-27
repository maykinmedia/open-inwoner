import register from 'preact-custom-element';
import { AnyComponent } from 'preact';
import { wcRegistry as wcRegistry } from './registry';
import {
  WebComponentContext,
  WebComponentKey,
  WebComponentRegisterOptions,
} from './types';
import { withIntlWc } from '@react/lib/decorators';

/**
 * Find all unique web component names on the current page
 * @returns a unique array of strings from the founded component names.
 */
export const findWebComponentsOnPage = (): WebComponentKey[] => {
  const selector = Object.keys(wcRegistry).join(',');
  const elements = document.querySelectorAll<HTMLElement>(selector);
  const foundComponents = [...elements].map(
    (el) => el.tagName.toLowerCase() as WebComponentKey
  );
  return Array.from(new Set(foundComponents));
};

/**
 * Create context objects for all elements of a specific component
 */
export const createContextsForComponent = (
  componentName: WebComponentKey
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
  tagName: WebComponentKey,
  propNames?: (keyof P)[],
  options: WebComponentRegisterOptions = { shadow: false, i18n: false }
): HTMLElement {
  if (customElements.get(tagName ?? '')) return undefined!;

  // Remove i18n from options before passing to preact-custom-element
  const { i18n, ...registerOptions } = options;

  // If i18n option is enabled, wrap the component with IntlProvider
  // This
  const ComponentToRegister = i18n ? withIntlWc(Component) : Component;

  return register(ComponentToRegister, tagName, propNames, registerOptions);
}
