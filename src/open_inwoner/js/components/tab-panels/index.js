export class TabPanel {
  static selector = '.login-tab--container'

  constructor(node) {
    this.node = node
    this.tabHeadersRow = node.querySelector('.tabs__headers')
    this.tabHeaders = node.querySelectorAll('.tab__header')
    this.tabContent = node.querySelectorAll('.tab__content')

    this.tabHeadersRow.addEventListener('click', (e) => {
      e.preventDefault() // Prevent 'other' tab__panel from disappearing immediately

      const target = e.target.closest('.tab__header')
      if (target) {
        const index = [...this.tabHeaders].indexOf(target)
        if (index !== -1) {
          this.hideContent()
          this.showContent(index)
        }
      }
    })
  }

  hideContent() {
    this.tabContent.forEach((item) => {
      item.classList.remove('active')
    })
    this.tabHeaders.forEach((item) => {
      item.classList.remove('active')
      item.setAttribute('aria-selected', 'false')
    })
  }

  showContent(index = 0) {
    this.tabContent.forEach((item, idx) => {
      if (idx === index) {
        item.classList.remove('hide')
        item.classList.add('active')
      } else {
        item.classList.add('hide')
        item.classList.remove('active')
      }
    })
    this.tabHeaders.forEach((item, idx) => {
      if (idx === index) {
        item.classList.add('active')
        item.setAttribute('aria-selected', 'true')
      } else {
        item.classList.remove('active')
      }
    })
  }
}

/**
 * Function to activate tab and panel
 * @param {HTMLElement} activeTab - The tab to be activated
 * @param {HTMLElement} activePanel - The panel to be activated
 * @param {NodeList} tabHeaders - All tab headers
 */
function activateTab(activeTab, activePanel, tabHeaders) {
  if (activeTab) {
    activeTab.classList.add('active')
    activeTab.setAttribute('aria-selected', 'true')
  }
  if (activePanel) {
    activePanel.classList.remove('hide')
    activePanel.classList.add('active')
  }

  tabHeaders.forEach((tabHeader) => {
    if (tabHeader !== activeTab) {
      tabHeader.classList.remove('active')
      tabHeader.setAttribute('aria-selected', 'false')
    }
  })

  document.querySelectorAll('.tab__content').forEach((panel) => {
    if (panel !== activePanel) {
      panel.classList.add('hide')
      panel.classList.remove('active')
    }
  })
}

/**
 * Default activation of tabs WITHOUT coming from external link.
 * Relies on instantiated TabPanel instances.
 */
window.addEventListener('load', () => {
  const hash = window.location.hash
  const zakelijkTab = document.getElementById('zakelijk_tab')
  const particulierTab = document.getElementById('particulier_tab')
  const particulierPanel = document.getElementById('particulier_panel')
  const zakelijkPanel = document.getElementById('zakelijk_panel')

  if (hash.includes('zakelijk')) {
    activateTab(
      zakelijkTab,
      zakelijkPanel,
      document.querySelectorAll('.tab__header[data-panel]')
    )
  } else {
    activateTab(
      particulierTab,
      particulierPanel,
      document.querySelectorAll('.tab__header[data-panel]')
    )
  }
})

/**
 * Controls which tabs are active
 */
document
  .querySelectorAll(TabPanel.selector)
  .forEach((tabpanel) => new TabPanel(tabpanel))
