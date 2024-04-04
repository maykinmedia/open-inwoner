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

const tabpanels = document.querySelectorAll(TabPanel.selector)
;[...tabpanels].forEach((tabpanel) => new TabPanel(tabpanel))

// Activate tab from hash on page load
// Relies on instantiated TabPanel instances
window.addEventListener('load', () => {
  const hash = window.location.hash
  if (hash) {
    const tabHeader = document.querySelector(`.tab__header[href="${hash}"]`)
    if (tabHeader) {
      const index = [...tabHeader.parentNode.children].indexOf(tabHeader)
      const tabPanel = tabHeader.closest('.tab--container')
      const tabPanelInstance = tabPanel && tabPanel.TabPanel
      if (tabPanelInstance) {
        tabPanelInstance.showContent(index)
      }
    }
  }
})
