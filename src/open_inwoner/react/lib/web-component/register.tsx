// The list of our react + web components
export const webcomponents = {
  'action-list': () => import('@react/components/ActionList/web-component'),
};

export async function registerWebComponents() {
  try {
    const entries = Object.entries(webcomponents);

    // Create a single selector string for all components
    const selector = entries.map(([name]) => name).join(',');
    const foundElements = document.querySelectorAll(selector);
    // Use Set to deduplicate tag names
    const uniqueTagNames = new Set(
      Array.from(foundElements).map(
        (el) => el.tagName.toLowerCase() as keyof typeof webcomponents
      )
    );
    // Load all unique components in parallel
    await Promise.all(
      Array.from(uniqueTagNames).map(async (name) => {
        // Skip if already defined
        if (customElements.get(name)) return;

        try {
          const importer = webcomponents[name];
          if (!importer)
            return console.error(
              `WebComponent ImportError: "${name}" has no web component import`
            );
          const { default: Component } = await importer();
          if (!Component)
            return console.error(
              `WebComponent ImportError: "${name}" has no default export`
            );
          customElements.define(name, Component);
        } catch (err) {
          console.error(`WebComponent LoadError: "${name}"`, err);
        }
      })
    );
  } catch (err) {
    console.error('Could not load WebComponents:', err);
  }
}
