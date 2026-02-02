import { AnyComponent as AC, h, render } from 'preact';
import register from 'preact-custom-element';
import { withIntlWebComponent } from '../decorators';
import {
  performancePlugin,
  silentErrorPlugin,
  skeletonPlugin,
} from './plugins';
import { WEB_COMPONENT_REGISTRY } from './registry';
import type {
  WebComponentContext,
  WebComponentPlugin,
  WebComponentRegisterOptions,
  WebComponentTagName,
} from '.';
import { ExtractGeneric } from '../types';

export type PreactCustomElement = HTMLElement & {
  _root: ShadowRoot | HTMLElement;
  _vdomComponent: AC;
  _vdom: ReturnType<typeof h> | null;
  _props: Record<string, unknown>;
  internals?: ElementInternals;
};

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
    // @ts-expect-error
    ...(window.IS_DEV ? [performancePlugin] : []),
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
  ): HTMLElement {
    // Extract our custom options
    const {
      i18n,
      internals: internalsConfig,
      formAssociated = false,
      ...registerOptions
    } = options;

    // If i18n option is enabled, wrap the component with IntlProvider
    const ComponentToRegister = i18n
      ? withIntlWebComponent(Component)
      : Component;

    ComponentToRegister.formAssociated = true;

    // ComponentToRegister.internals = {
    //   role: 'list',
    // };

    return register(ComponentToRegister, tagName, propNames, registerOptions);
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
    } catch (err) {
      console.error('[web-component:error]:', err);
    }
  }
}
