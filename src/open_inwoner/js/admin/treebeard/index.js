function collapseNode(node) {
  const event = new CustomEvent('click', {
    view: window,
    bubbles: true,
    detail: { system: true },
  });
  setTimeout(() => {
    node.dispatchEvent(event);
  }, 1);
}

function updateNodeStatus() {
  const buttons = document.querySelectorAll('a.treebeard-collapse');
  buttons.forEach((button) => {
    button.addEventListener('click', (event) => {
      if (event.detail.system) {
        return;
      }
      const nodeId = event.currentTarget.closest('tr')?.dataset.nodeId;
      if (!nodeId) {
        return;
      }
      setTimeout(() => {
        if (button.classList.contains('treebeard-expanded')) {
          window.localStorage.setItem(`${nodeId}-open`, true);
        } else {
          window.localStorage.removeItem(`${nodeId}-open`);
        }
      }, 100);
    });
  });
}

function expandOpenNodes() {
  const rows = document.querySelectorAll('#result_list tr');
  rows.forEach((row) => {
    const nodeId = row.dataset.nodeId;
    if (!nodeId) {
      return;
    }
    const currentRowOpen = window.localStorage.getItem(`${nodeId}-open`);
    if (currentRowOpen) {
      const button = row.querySelector('.treebeard-collapse');
      if (!button) {
        return;
      }
      const event = new MouseEvent('click', {
        view: window,
        bubbles: true,
      });
      setTimeout(() => {
        button.dispatchEvent(event);
      }, 1);
    }
  });
}

function main() {
  const questionnairePage = document.querySelector(
    ' .app-questionnaire, .model-questionnairestep, .change-list'
  );

  if (questionnairePage) {
    // Collapse all expanded nodes when the page is loaded
    [...document.querySelectorAll('a.treebeard-collapse')]
      .reverse()
      .forEach(collapseNode);

    // Update local storage when the node is expanded
    updateNodeStatus();

    // Expand all nodes which are saved as open in the local storage
    expandOpenNodes();
  }
}

window.addEventListener('load', main);
