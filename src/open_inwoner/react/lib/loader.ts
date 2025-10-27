import { AbstractPage } from '@react/lib/abstractPage'
import { registerWebComponents } from './wc/register'

interface ModuleWithInit {
  init(): Promise<void> | void
}

const modules = {
  demo: () => import('@react/modules/demo'),
  sidenav: () => import('@react/modules/SideNavModule/SideNavModule'),
  kvkbranchselector: () =>
    import('@react/modules/KVKBranchSelectorModule/KVKBranchSelectorModule'),
}

const loadModule = async (
  module: keyof typeof modules
): Promise<{ default: typeof AbstractPage | ModuleWithInit } | undefined> => {
  if (modules[module]) return modules[module]()
}

export default class ModuleLoader {
  static async load() {
    await registerWebComponents()

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
}
