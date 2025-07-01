/**
 * Router
 * Auto loads view based on page name, which is read from html tag data attribute
 */

/**
 * Load the relevant module dynamically.
 * @param name Alias of the page to load the module for.
 */
const loadModule = async (name: string) => {
  switch (name) {
    case 'demo':
      return import('../modules/demo')
    // some pages don't have an entrypoint at all, so don't throw exceptions
  }
}

export default class Router {
  static async route() {
    if (!this.page) return
    try {
      const pageModule = await loadModule(this.page)
      if (!pageModule?.default) return
      pageModule.default.init()
    } catch (exc) {
      console.error(exc)
    }
  }

  /**
   * Returns the current page name
   */
  static get page() {
    let html = document.querySelector('html')
    return html?.dataset.page
  }
}
