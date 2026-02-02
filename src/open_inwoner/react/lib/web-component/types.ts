/**
 * Web Component Type Definitions
 *
 * Core types used throughout the web component system.
 * These types are foundational and have no dependencies on the registry.
 */

import { AnyComponent as AC } from 'preact';
import { WEB_COMPONENT_REGISTRY } from './registry';
import { KebabCasedProperties } from 'type-fest';

/**
 * Context object passed to plugin hooks
 * Contains information about the component being loaded
 */
export interface WebComponentContext {
  /** The web component tag name (e.g., 'action-list') */
  componentName: string;
  /** The HTML element instance */
  element: HTMLElement;
}

/**
 * Function signature for plugin lifecycle hooks
 */
export type WebComponentLoadHook = (
  context: WebComponentContext,
  error?: Error
) => Promise<void> | void;

/**
 * Plugin interface for extending web component behavior
 * Plugins can hook into the loading lifecycle
 */
export interface WebComponentPlugin {
  /** Unique plugin identifier */
  readonly name: string;
  /**
   * Hook called before the web component is defined/loaded
   */
  beforeLoad?: WebComponentLoadHook;
  /**
   * Hook called after the web component is defined/loaded
   */
  afterLoad?: WebComponentLoadHook;
  /**
   * Hook called when an error occurs during loading
   */
  onError?: WebComponentLoadHook;
}

/**
 * Extra options for web component registration
 */
export type WebComponentRegisterExtraOptions = {
  /**
   * Whether to automatically wrap the component with IntlProvider for i18n support
   * @default false
   */
  i18n?: boolean;
};

/**
 * Extended options for web component registration
 * Supports both shadow DOM and light DOM configurations
 */
export type WebComponentRegisterOptions = WebComponentRegisterExtraOptions &
  (
    | { shadow: false }
    | {
        shadow: true;
        mode?: 'open' | 'closed';
        adoptedStyleSheets?: CSSStyleSheet[];
        serializable?: boolean;
      }
  );

/**
 * Web component definition with full configuration
 * Define this in each component's constants.ts file
 *
 * @example
 * ```ts
 * export const EXAMPLE_DEFINITION: WebComponentDefinition<IExampleProps, "oip-example"> = {
 *   tagName: 'oip-example',
 *   propNames: ['data', 'dataId'],
 *   options: { shadow: false },
 *   importer: () => import('./Example'),
 * };
 * ```
 */
export interface WebComponentDefinition<T extends string, P = {}> {
  /** The custom element tag name */
  tagName: T;
  /** Array of prop names to expose as HTML attributes */
  propNames: (keyof P)[];
  /** Registration options (shadow DOM, i18n, etc.) */
  options?: WebComponentRegisterOptions;
  /** Dynamic import function for lazy loading */
  importer: () => Promise<{
    default: AC<P>;
  }>;
}

/**
 * Valid web component tag names - derived from the registry keys
 */
export type WebComponentTagName = keyof typeof WEB_COMPONENT_REGISTRY;

/**
 * JSX Registry - automatically derived from WEB_COMPONENT_REGISTRY
 * Maps web component tag names to their kebab-cased prop types
 * This is used in web-components.d.ts to provide JSX typing
 */
export type WebComponentJSXRegistry = {
  [K in keyof typeof WEB_COMPONENT_REGISTRY]: KebabCasedProperties<
    (typeof WEB_COMPONENT_REGISTRY)[K] extends WebComponentDefinition<
      infer _S,
      infer P
    >
      ? P
      : never
  >;
};
