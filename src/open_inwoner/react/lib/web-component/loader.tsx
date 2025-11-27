import { wcRegistry } from './registry';
import {
  runAfterLoadHooks,
  runBeforeLoadHooks,
  runErrorHooks,
} from './middleware';
import { createContextsForComponent, findWebComponentsOnPage } from './utils';

/**
 * Load a single web component with plugin lifecycle
 */
export const wcLoader = async (name: string): Promise<void> => {
  // Skip if already defined
  if (customElements.get(name)) return;

  // Get the import function.
  const importer = wcRegistry[name];
  if (!importer) throw new Error(`"${name}" has no web component import`);

  // Get the context of the web components
  const contexts = createContextsForComponent(name);

  try {
    // Run plugins `beforeLoad` hooks
    await Promise.all(contexts.map((context) => runBeforeLoadHooks(context)));

    // Import and load the web component
    const { loader } = await importer();
    if (!loader) throw new Error(`"${name}" has no default export`);
    loader();

    // Run plugins `afterLoad` hooks
    await Promise.all(contexts.map((context) => runAfterLoadHooks(context)));
  } catch (err) {
    // Run plugins `onError` hooks
    contexts.forEach((context) => runErrorHooks(context, err as Error));
  }
};

/**
 * Main function to register all web components found on the page
 */
export const registerWebComponents = async (): Promise<void> => {
  try {
    // Look for all web components on the current page
    const founded = findWebComponentsOnPage();

    // Only continue if there are web components on the current page
    if (!founded.length) return;

    // Load all unique components in parallel
    await Promise.all(founded.map(wcLoader));
  } catch (err) {
    console.error('[wc:error]:', err);
  }
};
