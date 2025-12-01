import { AnyComponent } from 'preact';
import register from 'preact-custom-element';
import { withIntlWc } from '../decorators';
import {
  performancePlugin,
  silentErrorPlugin,
  skeletonPlugin,
} from './plugins';
import { WEB_COMPONENT_REGISTRY, WebComponentTagName } from './registry';
import type {
  WebComponentContext,
  WebComponentPlugin,
  WebComponentRegisterOptions,
} from './types';

export class WebComponentLoader {
  constructor() {}
  /**
   * Central registry
   * This is the single source of truth for all web components.
   *
   * To add a new web component:
   * 1. Create a COMPONENT_DEFINITION in the component's constants.ts
   * 2. Import the definition and tag name at the top of this file
   * 3. Add to WEB_COMPONENT_REGISTRY above
   */
  static registry = WEB_COMPONENT_REGISTRY;

  /**
   * Global plugins that run for all web components
   */
  private static pluginRegistry: WebComponentPlugin[] = [
    silentErrorPlugin,
    skeletonPlugin,
    // @ts-expect-error
    ...(window.IS_DEV ? [performancePlugin] : []),
  ];

  /**
   * Helper method to create a loader function for a web component
   * This is used for Storybook and testing
   */
  public static loadWC(
    tagName: WebComponentTagName,
    Component: AnyComponent<any, any>
  ) {
    return () => {
      const config = WebComponentLoader.registry[tagName];
      WebComponentLoader.registerWebComponent(
        Component,
        config.tagName,
        config.propNames,
        config.options
      );
    };
  }

  private static async importWC(name: WebComponentTagName): Promise<void> {
    // Skip if already defined
    if (customElements.get(name))
      return console.debug(
        `Custom element ${name} is already defined, aborting loading for this element`
      );

    // Get the import function.
    const { importer } = WebComponentLoader.registry[name];
    if (!importer) throw new Error(`"${name}" has no web component import`);

    // Get the context of the web components
    const contexts = WebComponentLoader.createContextsForComponent(name);

    try {
      // Run plugins `beforeLoad` hooks
      await Promise.all(contexts.map(WebComponentLoader.runBeforeLoadHooks));

      // Import and load the web component
      const { loader } = await importer();
      if (!loader) throw new Error(`"${name}" has no default export`);
      loader();

      // Run plugins `afterLoad` hooks
      await Promise.all(contexts.map(WebComponentLoader.runAfterLoadHooks));
    } catch (err) {
      // Run plugins `onError` hooks
      contexts.forEach((context) =>
        WebComponentLoader.runErrorHooks(context, err as Error)
      );
    }
  }

  /**
   * Find all unique web component names on the current page
   * @returns a unique array of strings from the founded component names.
   */
  private static findWebComponentsOnPage(): WebComponentTagName[] {
    const selector = Object.keys(WebComponentLoader.registry).join(',');
    const elements = document.querySelectorAll<HTMLElement>(selector);
    const foundComponents = [...elements].map((el) => el.tagName.toLowerCase());
    return Array.from(new Set(foundComponents)) as WebComponentTagName[];
  }

  /**
   * Create context objects for all elements of a specific component
   */
  static createContextsForComponent(
    componentName: string
  ): WebComponentContext[] {
    const elements = document.querySelectorAll<HTMLElement>(componentName);
    return [...elements].map((element) => ({ componentName, element }));
  }

  private static async runBeforeLoadHooks(context: WebComponentContext) {
    for (const plugin of WebComponentLoader.pluginRegistry) {
      try {
        await plugin.beforeLoad?.(context);
      } catch (error) {
        console.error(
          `[Plugin:${plugin.name}] beforeLoad hook failed for ${context.componentName}:`,
          error
        );
      }
    }
  }

  private static async runAfterLoadHooks(context: WebComponentContext) {
    for (const plugin of WebComponentLoader.pluginRegistry) {
      try {
        await plugin.afterLoad?.(context);
      } catch (error) {
        console.error(
          `[Plugin:${plugin.name}] afterLoad hook failed for ${context.componentName}:`,
          error
        );
      }
    }
  }

  /**
   * Error hook runner used to execute the onError plugin function
   * @param context
   * @param error The error that occured.
   */
  private static async runErrorHooks(
    context: WebComponentContext,
    error: Error
  ) {
    if (!error) return;

    for (const plugin of WebComponentLoader.pluginRegistry) {
      try {
        plugin.onError?.(context, error);
      } catch (pluginError) {
        console.error(
          `[Plugin:${plugin.name}] onError hook failed for ${context.componentName}:`,
          pluginError
        );
      }
    }
  }

  /**
   * Register the webcomponents on the current page
   * @returns
   */
  static async registerWebComponents() {
    try {
      // Look for all web components on the current page
      const founded = WebComponentLoader.findWebComponentsOnPage();

      // Only continue if there are web components on the current page
      if (!founded.length) return;

      // Load all unique components in parallel
      await Promise.all(founded.map(WebComponentLoader.importWC));
    } catch (err) {
      console.error('[wc:error]:', err);
    }
  }

  static registerWebComponent<P = {}, S = {}>(
    Component: AnyComponent<P, S>,
    tagName: string,
    propNames?: (keyof P)[],
    options: WebComponentRegisterOptions = { shadow: false, i18n: false }
  ): HTMLElement {
    if (customElements.get(tagName)) return undefined!;

    // Remove i18n from options before passing to preact-custom-element
    const { i18n, ...registerOptions } = options;

    // If i18n option is enabled, wrap the component with IntlProvider
    // This
    const ComponentToRegister = i18n ? withIntlWc(Component) : Component;

    return register(ComponentToRegister, tagName, propNames, registerOptions);
  }
}
