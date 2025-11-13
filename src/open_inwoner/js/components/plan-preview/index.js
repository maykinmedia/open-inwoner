import Modal from '../modal';

export class PlanPreview {
  // Selector for elements triggering the preview modal
  static selector = '.show-preview';

  constructor(node) {
    this.node = node;
    this.node.addEventListener('click', this.openPreview.bind(this));
  }

  openPreview(event) {
    event.stopPropagation();
    event.preventDefault();

    const modalId = this.node.dataset.id || 'modal';
    const modalElement = document.getElementById(modalId);
    if (!modalElement) {
      return;
    }

    const modal = new Modal(modalElement);
    modal.setModalIcons(false);
    modal.setConfirmButtonVisibility(false);
    modal.setCancelButtonVisibility(true);
    modal.setButtonIconCloseVisibility(true);

    // Track element that opened the modal
    modal.openedBy = this.node;

    // Find corresponding radio input
    let radioInput = null;
    let radioLabel = null;

    // Find 'old' radio inputs structure so new and old can co-exist
    // TODO: remove modal selectors for old way to display plan-template choices
    const templateRow = this.node.closest('.plan-template__row');
    if (templateRow) {
      radioInput = templateRow.querySelector('.radio__input');
      radioLabel = templateRow.querySelector('.radio__label');
    }

    // Find new radio choice-list structure
    // TODO: remove redundant clarifications for new structure
    if (!radioInput) {
      const choiceListItem = this.node.closest('.choice-list__item');
      if (choiceListItem) {
        radioInput = choiceListItem.querySelector('.choice-list__radio');
        radioLabel = choiceListItem.querySelector('.choice-list__label');
      }
    }

    const templateId = modalId.split('-')[1];

    // As a fallback, try to find the radio by its ID
    if (!radioInput && templateId) {
      radioInput = document.getElementById(`id_template_${templateId}`);
      if (radioInput) {
        radioLabel = document.querySelector(
          `label[for="id_template_${templateId}"]`
        );
        if (!radioLabel) {
          // If no explicit label found, look for parent or ancestor label
          radioLabel =
            radioInput.closest('label') ||
            radioInput.parentElement.querySelector('label');
        }
      }
    }

    // Close buttons NOT selecting a radio input
    const noSelectionCloseButtons = modalElement.querySelectorAll(
      '.modal--no-reset .modal__actions--align-right .button--textless.button--transparent'
    );

    noSelectionCloseButtons.forEach((button) => {
      button.addEventListener(
        'click',
        (event) => {
          event.preventDefault();
          modal.hide(); // Only close the modal
        },
        { once: true }
      );
    });

    // Buttons that SHOULD select a radio input when closing modal
    const selectionButtons = modalElement.querySelectorAll(
      '.modal--no-reset .modal__actions--align-right .button--primary'
    );

    if (radioInput) {
      selectionButtons.forEach((button) => {
        button.addEventListener(
          'click',
          () => {
            // Select the radio input
            radioInput.checked = true;

            // Set focus to the radio input to trigger CSS focus styles
            radioInput.focus();

            // If using the choice-list structure, add the 'selected' class to the parent list item
            const choiceListItem = radioInput.closest('.choice-list__item');
            if (choiceListItem) {
              // Remove 'selected' class from all items
              document
                .querySelectorAll('.choice-list__item')
                .forEach((item) => item.classList.remove('selected'));

              // Add 'selected' class to the clicked item
              choiceListItem.classList.add('selected');
            }

            // Trigger change event to notify any listeners
            const changeEvent = new Event('change', { bubbles: true });
            radioInput.dispatchEvent(changeEvent);

            // Delay focus update for accessibility to ensure DOM updates are processed
            setTimeout(() => {
              // Ensure focus affects the label for visual feedback
              if (
                radioLabel &&
                radioLabel.getAttribute('for') === radioInput.id
              ) {
                radioLabel.focus();
              } else {
                radioInput.focus();
              }
            }, 50);

            modal.hide(); // Close modal after selection
          },
          { once: true }
        );
      });
    }

    // Set modal close behavior without auto-selecting a radio input
    modal.setModalClosedCallback(() => {
      if (radioInput && radioInput.checked) {
        // Try to focus the label first (if it exists and is properly linked)
        if (radioLabel && radioLabel.getAttribute('for') === radioInput.id) {
          radioLabel.focus();
        } else {
          // Fall back to focusing the input itself
          radioInput.focus();
        }
      } else if (modal.openedBy) {
        // If no radio was selected, return focus to the element that opened the modal
        modal.openedBy.focus();
      }
    });

    modal.show();
  }
}

document
  .querySelectorAll(PlanPreview.selector)
  .forEach((previewNode) => new PlanPreview(previewNode));
