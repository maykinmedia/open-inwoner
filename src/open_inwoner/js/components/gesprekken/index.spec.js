import { beforeAll, beforeEach, describe, expect, it } from 'vitest';

function poll(elt) {
  const event = new CustomEvent('htmx:beforeRequest', {
    bubbles: true,
    cancelable: true,
    detail: { elt },
  });
  elt.dispatchEvent(event);
  return event.defaultPrevented;
}

describe('Mijn gesprekken polling', () => {
  beforeAll(async () => {
    await import('./index');
  });

  beforeEach(() => {
    document.body.innerHTML = `
      <section id="gesprekken">
        <details class="gesprekken__start"><summary>Nieuw gesprek</summary></details>
        <textarea name="tekst"></textarea>
        <button id="tab" type="button">Gesloten</button>
      </section>`;
  });

  const sectie = () => document.getElementById('gesprekken');

  it('polls when the resident is not doing anything', () => {
    expect(poll(sectie())).toBe(false);
  });

  it('skips polling while a message is typed', () => {
    document.querySelector('textarea').value = 'Hallo';
    expect(poll(sectie())).toBe(true);
  });

  it('skips polling while the textarea has focus', () => {
    document.querySelector('textarea').focus();
    expect(poll(sectie())).toBe(true);
  });

  it('skips polling while the start form is open', () => {
    document.querySelector('details').open = true;
    expect(poll(sectie())).toBe(true);
  });

  it('never blocks other requests, such as switching tabs', () => {
    document.querySelector('textarea').value = 'Hallo';
    expect(poll(document.getElementById('tab'))).toBe(false);
  });
});
