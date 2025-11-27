/**
 * Context object passed to plugin hooks
 */
export interface WebComponentContext {
  /** The web component tag name (e.g., 'simple-header') */
  componentName: string;
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

/**
 * Type for component importer functions
 */
export type WebComponentImporter = () => Promise<{ loader: () => void }>;

/**
 * Registry of web components
 */
export type WebComponentRegistry = Record<string, WebComponentImporter>;

/**
 * Function that executes a load hook
 */
export type WebComponentLoadHook = (
  context: WebComponentContext,
  error?: Error
) => Promise<void> | void;
