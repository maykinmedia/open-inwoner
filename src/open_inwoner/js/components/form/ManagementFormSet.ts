// Generic client-side helpers for a Django formset: its management form
// (TOTAL_FORMS / MAX_NUM_FORMS) plus adding and renumbering rows cloned from
// the formset's empty-form <template>. No knowledge of any specific form's
// fields lives here.

/**
 * Wraps the DOM of a single Django formset, conventionally rendered as a
 * container carrying `data-prefix` with:
 *  - `#<prefix>-entries`     - the rows container,
 *  - `#<prefix>-empty-row`   - a <template> of the empty form,
 *  - the management-form inputs (`<prefix>-TOTAL_FORMS`, `-MAX_NUM_FORMS`).
 *
 * Exposes the form count/limit and the two index-sensitive mutations (add and
 * renumber); anything field-specific stays with the caller.
 */
export class ManagementFormSet {
  private constructor(
    readonly prefix: string,
    readonly entriesContainer: HTMLElement,
    private readonly template: HTMLTemplateElement,
    private readonly totalFormsInput: HTMLInputElement,
    private readonly maxFormsInput: HTMLInputElement | null,
    private readonly rowSelector: string
  ) {}

  /**
   * Build a ManagementFormSet from its container, or null when a required
   * element is missing (so callers can bail out of enhancement).
   */
  static create(
    container: HTMLElement,
    rowSelector: string
  ): ManagementFormSet | null {
    const prefix = container.dataset.prefix;
    if (!prefix) return null;
    const entriesContainer = container.querySelector<HTMLElement>(
      `#${prefix}-entries`
    );
    const template = container.querySelector<HTMLTemplateElement>(
      `#${prefix}-empty-row`
    );
    const totalForms = container.querySelector<HTMLInputElement>(
      `[name="${prefix}-TOTAL_FORMS"]`
    );
    if (!entriesContainer || !template || !totalForms) return null;

    return new ManagementFormSet(
      prefix,
      entriesContainer,
      template,
      totalForms,
      container.querySelector<HTMLInputElement>(
        `[name="${prefix}-MAX_NUM_FORMS"]`
      ),
      rowSelector
    );
  }

  get total(): number {
    return parseInt(this.totalFormsInput.value, 10) || 0;
  }

  private set total(value: number) {
    this.totalFormsInput.value = String(value);
  }

  get max(): number {
    const value = this.maxFormsInput?.value;
    return value ? parseInt(value, 10) : Infinity;
  }

  get isFull(): boolean {
    return this.total >= this.max;
  }

  get rowElements(): HTMLElement[] {
    return Array.from(
      this.entriesContainer.querySelectorAll<HTMLElement>(this.rowSelector)
    );
  }

  /**
   * Clone the empty-form template, index it at the next position and append it.
   * Returns the new row element, or null when the formset is already full.
   */
  addForm(): HTMLElement | null {
    if (this.isFull) return null;

    const index = this.total;
    const fragment = this.template.content.cloneNode(true) as DocumentFragment;
    this.setFormIndex(fragment, this.prefix, index);

    const row = fragment.querySelector<HTMLElement>(this.rowSelector);
    this.entriesContainer.appendChild(fragment);
    this.total = index + 1;
    return row;
  }

  /** Renumber every row sequentially and sync TOTAL_FORMS to the row count. */
  reindex(): void {
    const rows = this.rowElements;
    rows.forEach((row, index) => this.setFormIndex(row, this.prefix, index));
    this.total = rows.length;
  }

  /**
   * Rewrite the "<prefix>-<index>-" segment in every name/id/for attribute under
   * `root`, so a cloned or moved row matches the index Django expects.
   */
  setFormIndex(root: ParentNode, prefix: string, index: number): void {
    const pattern = new RegExp(`${prefix}-(?:\\d+|__prefix__)-`);
    const replacement = `${prefix}-${index}-`;

    root.querySelectorAll<HTMLElement>('[name],[id],[for]').forEach((el) => {
      for (const attr of ['name', 'id', 'for'] as const) {
        const value = el.getAttribute(attr);
        if (value) el.setAttribute(attr, value.replace(pattern, replacement));
      }
    });
  }
}
