import { wcPluginRegistry } from './registry';
import type { WebComponentLoadHook } from './types';

/**
 * Run beforeLoad hooks for applicable plugins
 */
export const runBeforeLoadHooks: WebComponentLoadHook = async (context) => {
  for (const plugin of wcPluginRegistry) {
    try {
      await plugin.beforeLoad?.(context);
    } catch (error) {
      console.error(
        `[Plugin:${plugin.name}] beforeLoad hook failed for ${context.componentName}:`,
        error
      );
    }
  }
};

/**
 * Run afterLoad hooks for applicable plugins
 */
export const runAfterLoadHooks: WebComponentLoadHook = async (context) => {
  for (const plugin of wcPluginRegistry) {
    try {
      await plugin.afterLoad?.(context);
    } catch (error) {
      console.error(
        `[Plugin:${plugin.name}] afterLoad hook failed for ${context.componentName}:`,
        error
      );
    }
  }
};

/**
 * Run error hooks for applicable plugins
 */
export const runErrorHooks: WebComponentLoadHook = (context, error) => {
  if (!error) return;

  for (const plugin of wcPluginRegistry) {
    try {
      plugin.onError?.(context, error);
    } catch (pluginError) {
      console.error(
        `[Plugin:${plugin.name}] onError hook failed for ${context.componentName}:`,
        pluginError
      );
    }
  }
};
