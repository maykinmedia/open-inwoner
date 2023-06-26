export class TabPanel {
  static selector = '.tab--container'

  constructor(node) {
    this.node = node
    this.tabHeadersRow = node.querySelector('.tabs__headers')
    this.tabHeaders = node.querySelectorAll('.tab__header')
    this.tabContent = node.querySelectorAll('.tab__content')

    this.hideContent()
    this.showContent()

    this.tabHeadersRow.addEventListener('click', (e) => {
      const target = e.target
      if (target.classList.contains('tab__header')) {
        console.log('there is a tabheader')
        this.tabHeaders.forEach((item, i) => {
          if (target == item) {
            this.hideContent()
            this.showContent(i)
          }
        })
      }
    })
  }

  hideContent() {
    console.log('Hide tab...')
    this.tabContent.forEach((item) => {
      item.classList.add('hide')
      item.classList.remove('active')
    })
    this.tabHeaders.forEach((item) => {
      item.classList.remove('active')
    })
  }

  showContent(i = 0) {
    console.log('Show tab...')
    this.tabContent[i].classList.add('active')
    this.tabContent[i].classList.remove('hide')
    this.tabHeaders[i].classList.add('active')
  }
}

const tabpanels = document.querySelectorAll(TabPanel.selector)
;[...tabpanels].forEach((tabpanel) => new TabPanel(tabpanel))
