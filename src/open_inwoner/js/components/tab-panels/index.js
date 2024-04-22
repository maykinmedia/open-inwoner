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
      item.classList.add('hide')
      item.classList.remove('active')
    })
    this.tabHeaders.forEach((item) => {
      item.classList.remove('active')
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
      } else {
        item.classList.remove('active')
      }
    })
  }
}

/**
 * Controls which tabs are active
 */
document
  .querySelectorAll(TabPanel.selector)
  .forEach((tabpanel) => new TabPanel(tabpanel))

/**
 * Activate Zakelijk tab from hash on page load, when coming from external link.
 * Relies on instantiated TabPanel instances.
 */
window.addEventListener('load', () => {
  const tabHeaders = document.querySelectorAll('.tab__header[data-panel]')
  tabHeaders.forEach((tabHeader) => {
    const panelId = tabHeader.dataset.panel
    const panel = document.getElementById(panelId)
    if (panel) {
      tabHeader.addEventListener('click', () => {
        // Hide all panels, ensuring only one panel is visible at a time
        document.querySelectorAll('.tab__content').forEach((panel) => {
          panel.classList.remove('active')
        })
        // Activate panel
        panel.classList.add('active')
        // Activate tab
        tabHeaders.forEach((header) => {
          header.classList.remove('active')
        })
        tabHeader.classList.add('active')
      })
    }
  })
})
