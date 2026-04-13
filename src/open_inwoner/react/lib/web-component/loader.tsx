import { AnyComponent as AC } from 'preact';
import type {
  WebComponentContext,
  WebComponentPlugin,
  WebComponentRegisterOptions,
  WebComponentTagName,
} from '.';
import { withIntl } from '../decorators';
import { ExtractGeneric } from '../types';
import {
  performancePlugin,
  silentErrorPlugin,
  skeletonPlugin,
} from './plugins';
import { register } from '@maykinmedia/preact-custom-element';
import { WEB_COMPONENT_REGISTRY } from './registry';

export class WebComponentLoader {
  constructor() {}
  /**
   * Central registry
   */
  static registry = WEB_COMPONENT_REGISTRY;

  /**
   * Global plugins that run for all web components
   */
  private static pluginRegistry: WebComponentPlugin[] = [
    silentErrorPlugin,
    skeletonPlugin,
    // @ts-expect-error window.IS_DEV is a custom window variable which we set in the master template.
    ...(window.IS_DEV || import.meta.env.DEV || import.meta.env.STORYBOOK
      ? [performancePlugin]
      : []),
  ];

  /**
   * Find all unique web component names on the current page
   * @returns a unique array of strings from the found component names.
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
  private static createContextsForComponent(
    componentName: string
  ): WebComponentContext[] {
    const elements = document.querySelectorAll<HTMLElement>(componentName);
    return [...elements].map((element) => ({ componentName, element }));
  }

  /**
   * Before load runner used to execute the beforeLoad plugin function
   * @param context
   */
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

  /**
   * After load runner used to execute the afterLoad plugin function
   * @param context
   */
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

  private static registerWebComponent<P = {}>(
    Component: AC<P>,
    tagName: string,
    propNames?: (keyof P)[],
    options: WebComponentRegisterOptions = { shadow: false, i18n: false }
  ) {
    // Remove i18n from options before passing to preact-custom-element
    const { i18n, ...registerOptions } = options;

    // Every custom element gets its own Preact render root, so the story/app-level
    // IntlProvider context is not accessible. Wrap with IntlProvider inside the
    // component itself whenever i18n is enabled.
    const ComponentToRegister = i18n ? withIntl(Component) : Component;

    // Fail silently if component is already defined.
    // The component continue rendering like nothing happened.
    try {
      return register(ComponentToRegister, tagName, propNames, registerOptions);
    } catch {
      return;
    }
  }

  public static async importWebComponent(
    name: WebComponentTagName
  ): Promise<void> {
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
      const { default: Component } = await importer();
      if (!Component) throw new Error(`"${name}" has no default export`);

      const config = WebComponentLoader.registry[name];

      WebComponentLoader.registerWebComponent<ExtractGeneric<typeof Component>>(
        Component as AC<ExtractGeneric<typeof Component>>,
        config.tagName,
        config.propNames as (keyof ExtractGeneric<typeof Component>)[],
        config.options
      );

      // Register sub-components immediatly.
      // The sub-components mount later when the loading is already done.
      if (config.subComponents) {
        await Promise.all(
          config.subComponents.map(WebComponentLoader.importWebComponent)
        );
      }
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
   * Register the webcomponents on the current page
   * @returns
   */
  static async registerWebComponents() {
    try {
      // Look for all web components on the current page
      const foundComponents = WebComponentLoader.findWebComponentsOnPage();

      // Only continue if there are web components on the current page
      if (!foundComponents.length) return;

      // Load all unique components in parallel
      await Promise.all(
        foundComponents.map(WebComponentLoader.importWebComponent)
      );

      // WebComponentLoader.registerWebComponents();
    } catch (err) {
      console.error('[web-component:error]:', err);
    }
  }
}
