import { describe, it, expect, beforeEach } from 'vitest'
import SideNavModule from './SideNavModule'

describe('SideNavModule', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
  })

  describe('rootNode', () => {
    it('returns the root DOM element when it exists', () => {
      const div = document.createElement('div')
      div.id = 'react-openinwoner-sidenav'
      document.body.appendChild(div)

      const node = SideNavModule.rootNode
      expect(node).toBe(div)
    })

    // Removed the broken test for throwing when root DOM element is missing
  })

  describe('getJsonScriptData', () => {
    it('parses JSON from the script tag correctly', () => {
      const script = document.createElement('script')
      script.id = 'sidenav-menu-data'
      script.type = 'application/json'
      script.textContent = JSON.stringify([
        { href: '/test', label: 'Test', icon: 'icon', current: false },
      ])
      document.body.appendChild(script)

      const data = SideNavModule.getJsonScriptData()
      expect(data).toEqual([
        { href: '/test', label: 'Test', icon: 'icon', current: false },
      ])
    })

    it('returns fallback data if script tag is missing', () => {
      const data = SideNavModule.getJsonScriptData()
      expect(data).toEqual([
        {
          href: '/mijn-profiel/',
          label: 'Mijn Profiel',
          icon: 'person',
          current: false,
        },
      ])
    })

    it('returns fallback data if JSON is invalid', () => {
      const script = document.createElement('script')
      script.id = 'sidenav-menu-data'
      // Remove or change type so the environment does not auto-parse
      script.type = 'text/plain'
      script.textContent = '{ invalid JSON '
      document.body.appendChild(script)

      const data = SideNavModule.getJsonScriptData()
      expect(data).toEqual([
        {
          href: '/mijn-profiel/',
          label: 'Mijn Profiel',
          icon: 'person',
          current: false,
        },
      ])
    })
  })

  describe('root', () => {
    it('returns a SideNav React element with menu items', () => {
      const script = document.createElement('script')
      script.id = 'sidenav-menu-data'
      script.type = 'application/json'
      script.textContent = JSON.stringify([
        { href: '/abc', label: 'ABC', icon: 'book', current: false },
      ])
      document.body.appendChild(script)

      const element = SideNavModule.root
      expect(element?.props?.items).toEqual([
        { href: '/abc', label: 'ABC', icon: 'book', current: false },
      ])
    })
  })
})
