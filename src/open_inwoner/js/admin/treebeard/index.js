function collapseNode(node) {
  const event = new CustomEvent('click', {
    view: window,
    bubbles: true,
    detail: { system: true },
  })
  setTimeout(() => {
    node.dispatchEvent(event)
  }, 1)
}

function updateNodeStatus() {
  const buttons = document.querySelectorAll('a.collapse')
  buttons.forEach((button) => {
    button.addEventListener('click', (event) => {
      if (event.detail.system) {
        return
      }
      const buttonId = event.currentTarget.parentElement.parentElement.id
      setTimeout(() => {
        if (button.classList.contains('expanded')) {
          window.localStorage.setItem(`${buttonId}-open`, true)
        } else {
          window.localStorage.removeItem(`${buttonId}-open`)
        }
      }, 100)
    })
  })
}

function expandOpenNodes() {
  const rows = document.querySelectorAll('#result_list tr')
  rows.forEach((row) => {
    const currentRowOpen = window.localStorage.getItem(`${row.id}-open`)
    if (currentRowOpen) {
      const button = row.querySelector('.collapse')
      const event = new MouseEvent('click', {
        view: window,
        bubbles: true,
      })
      setTimeout(() => {
        button.dispatchEvent(event)
      }, 1)
    }
  })
}

function main() {
  const questionnairePage = document.querySelector(
    ' .app-questionnaire, .model-questionnairestep, .change-list'
  )

  if (questionnairePage) {
    // Collapse all expanded nodes when the page is loaded
    ;[...document.querySelectorAll('a.collapse')]
      .reverse()
      .forEach(collapseNode)

    // Update local storage when the node is expanded
    updateNodeStatus()

    // Expand all nodes which are saved as open in the local storage
    expandOpenNodes()
  }
}

window.addEventListener('load', main)
