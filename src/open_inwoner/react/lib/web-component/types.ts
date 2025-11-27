import { wcRegistry } from '.';

export type WebComponentKey = keyof typeof wcRegistry;

/**
 * Context object passed to plugin hooks
 */
export interface WebComponentContext {
  /** The web component tag name (e.g., 'action-list') */
  componentName: WebComponentKey;
  /** The HTML element instance */
  element: HTMLElement;
}

/**
 * Plugin interface for extending web component behavior
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

// /**
//  * Type for component importer functions
//  */
// export type WebComponentImporter = () => Promise<{ loader: () => void }>;

// /**
//  * Registry of web components
//  */
// export type WebComponentRegistry = Record<
//   WebComponentKey,
//   WebComponentImporter
// >;

/**
 * Function that executes a load hook
 */
export type WebComponentLoadHook = (
  context: WebComponentContext,
  error?: Error
) => Promise<void> | void;

/**
 * Extended options for web component registration
 */
export type WebComponentRegisterOptions =
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
