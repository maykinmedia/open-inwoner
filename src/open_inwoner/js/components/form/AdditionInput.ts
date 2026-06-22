// AdditionInput - repeatable input group (e.g. email addresses, phone numbers)
// backed by a Django (inline) formset.
//
// Template: components/Form/AdditionInput.html + AdditionInputRow.html
// Tag:      form_tags.py:addition_input
//
// Generic formset bookkeeping (management form, add, renumber) lives in
// ManagementFormSet; this file holds the DigitalAddress-specific behaviour:
//  - FormsetRow    - one entry: its fields and delete/primary behaviour.
//  - AdditionInput - wires events and orchestrates the collection of rows.

import { ManagementFormSet } from './ManagementFormSet';

const ROW_SELECTOR = '[data-addition-input-row]';
const DELETE_TRIGGER = '[data-delete-row]';
const PRIMARY_SUFFIX = '-is_standard_for_type';

/** A single formset entry, wrapping its row element and form fields. */
class FormsetRow {
  constructor(readonly element: HTMLElement) {}

  private getField(suffix: string): HTMLInputElement | null {
    return this.element.querySelector<HTMLInputElement>(`[name$="-${suffix}"]`);
  }

  /** Show or hide this row's delete button (the primary row is not removable). */
  setRemovable(value: boolean): void {
    const button =
      this.element.querySelector<HTMLButtonElement>(DELETE_TRIGGER);
    if (button) button.hidden = !value;
  }

  /** The "set as preferred" checkbox; exposed so callers can compare identity. */
  get primaryInput(): HTMLInputElement | null {
    return this.getField('is_standard_for_type');
  }

  get isPrimary(): boolean {
    return this.primaryInput?.checked ?? false;
  }

  setPrimary(value: boolean): void {
    if (this.primaryInput) this.primaryInput.checked = value;
  }

  /** Persisted rows carry a pk; rows added client-side do not. */
  get isPersisted(): boolean {
    return Boolean(this.getField('id')?.value);
  }

  get isDeleted(): boolean {
    return this.getField('DELETE')?.checked ?? false;
  }

  /** Flag a persisted row for server-side deletion and hide it from view. */
  markDeleted(): void {
    const deleteInput = this.getField('DELETE');
    if (deleteInput) deleteInput.checked = true;
    this.element.hidden = true;
  }

  remove(): void {
    this.element.remove();
  }
}

export class AdditionInput {
  static selector = '[data-addition-input]';

  /**
   * Enhance a container, or return null when its formset or add button is
   * missing (so callers can skip enhancement), mirrors ManagementFormSet.create.
   */
  static init(container: HTMLElement): AdditionInput | null {
    const formset = ManagementFormSet.create(container, ROW_SELECTOR);
    const addButton = container.dataset.prefix
      ? container.querySelector<HTMLButtonElement>(
          `#${container.dataset.prefix}-add-btn`
        )
      : null;

    if (!formset || !addButton) return null;
    return new AdditionInput(formset, addButton);
  }

  private constructor(
    private readonly formset: ManagementFormSet,
    private readonly addButton: HTMLButtonElement
  ) {
    this.addButton.addEventListener('click', this.onAdd);
    this.formset.entriesContainer.addEventListener('click', this.onDeleteClick);
    this.formset.entriesContainer.addEventListener(
      'change',
      this.onPrimaryChange
    );
    this.refresh();
  }

  private get rows(): FormsetRow[] {
    return this.formset.rowElements.map((element) => new FormsetRow(element));
  }

  /** Active rows are those not flagged for deletion. */
  private get activeRows(): FormsetRow[] {
    return this.rows.filter((row) => !row.isDeleted);
  }

  private onAdd = (event: Event): void => {
    event.preventDefault();
    this.formset.addForm();
    this.refresh();
  };

  private onDeleteClick = (event: Event): void => {
    const trigger = (event.target as HTMLElement).closest(DELETE_TRIGGER);
    if (!trigger) return;

    event.preventDefault();
    const element = trigger.closest<HTMLElement>(ROW_SELECTOR);
    if (element) this.deleteRow(new FormsetRow(element));
  };

  private deleteRow(row: FormsetRow): void {
    // The primary row is not removable, guaranteeing one entry stays checked.
    if (row.isPrimary) return;

    if (row.isPersisted) {
      // Let the server delete it on submit; keep its index intact.
      row.markDeleted();
    } else {
      // Unsaved row: drop it and renumber the remaining rows.
      row.remove();
      this.formset.reindex();
    }

    this.refresh();
  }

  /**
   * Single-selection (radio-like) behaviour: the clicked entry becomes the only
   * primary one. Re-checking the target also covers "click the primary entry
   * again" - the browser unchecks it, we set it back, so it can never deselect.
   */
  private onPrimaryChange = (event: Event): void => {
    const target = event.target as HTMLInputElement;
    if (!target.name.endsWith(PRIMARY_SUFFIX)) return;

    this.rows.forEach((row) => row.setPrimary(row.primaryInput === target));
    this.refresh();
  };

  /** Guarantee exactly one active row stays primary when any rows exist. */
  private ensurePrimary(): void {
    const active = this.activeRows;
    if (active.length && !active.some((row) => row.isPrimary)) {
      active[0].setPrimary(true);
    }
  }

  /**
   * Re-apply the component's invariants after any mutation:
   *  - exactly one active row is the primary,
   *  - the primary row's delete button is hidden (so a checked row always remains),
   *  - the add button is hidden once the formset is full.
   */
  private refresh(): void {
    this.ensurePrimary();
    this.rows.forEach((row) => row.setRemovable(!row.isPrimary));
    this.addButton.hidden = this.formset.isFull;
  }
}

document
  .querySelectorAll<HTMLElement>(AdditionInput.selector)
  .forEach((el) => AdditionInput.init(el));
