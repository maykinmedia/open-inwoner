import { AbstractPage } from '@react/lib/abstractPage'

interface ModuleWithInit {
  init(): Promise<void> | void
}

const modules = {
  demo: () => import('@react/modules/demo'),
  sidenav: () => import('@react/modules/SideNavModule/SideNavModule'),
  kvkbranchselector: () =>
    import('@react/modules/KVKBranchSelectorModule/KVKBranchSelectorModule'),
}

// The list of our react + web components
const webcomponents = {
  'action-list': () => import('@react/components/ActionList/web-component'),
}

const loadModule = async (
  module: keyof typeof modules
): Promise<{ default: typeof AbstractPage | ModuleWithInit } | undefined> => {
  if (modules[module]) return modules[module]()
}

export default class ModuleLoader {
  static async load() {
    await this.detectWebComponents()

    if (!this.modules.length) return
    try {
      for (const module of this.modules) {
        const pageModule = await loadModule(module)
        if (!pageModule?.default) return
        await pageModule.default.init()
      }
    } catch (exc) {
      console.error(exc)
    }
  }

  static get modules(): (keyof typeof modules)[] {
    const html = document.querySelector('html')
    try {
      return JSON.parse(html?.dataset.mountModules ?? '[]') ?? []
    } catch {
      return []
    }
  }

  // auto-detect the usage of a webcomponent on the page.
  // if there is one import the needed script and define the component.
  static async detectWebComponents() {
    for (const wc of Object.entries(webcomponents)) {
      const [name, importer] = wc
      const found = document.querySelector(name)
      if (!found) continue
      const { default: Component } = await importer()
      customElements.define(name, Component)
    }
  }
}
