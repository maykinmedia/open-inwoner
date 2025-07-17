import { AbstractPage } from '@react/lib/abstractPage'

/**
 * Loader
 * Auto loads view based on module name, which is read from html tag data attribute
 */

const modules = {
  demo: () => import('@react/modules/demo'),
  sidenav: () => import('@react/modules/Sidenav'),
}

/**
 * Load the relevant module dynamically.
 * @param module Alias of the page to load the module for.
 */
const loadModule = async (
  module: keyof typeof modules
): Promise<{ default: typeof AbstractPage } | undefined> => {
  if (modules[module]) return modules[module]()
}

export default class ModuleLoader {
  static async load() {
    if (!this.modules.length) return
    try {
      for (const module of this.modules) {
        const pageModule = await loadModule(module)
        if (!pageModule?.default) return
        pageModule.default.init()
      }
    } catch (exc) {
      console.error(exc)
    }
  }

  /**
   * Returns the modules that will be mounted to the html
   */
  static get modules(): (keyof typeof modules)[] {
    const html = document.querySelector('html')

    try {
      return JSON.parse(html?.dataset.mountModules ?? '[]') ?? []
    } catch {
      return []
    }
  }
}
