import {
  afterEach,
  beforeAll,
  beforeEach,
  describe,
  expect,
  it,
  vi,
  type Mock,
} from 'vitest';
import { BfcacheReloader } from './index';

function dispatchPageShow(persisted: boolean): void {
  const event = new Event('pageshow') as PageTransitionEvent;
  Object.defineProperty(event, 'persisted', { value: persisted });
  window.dispatchEvent(event);
}

describe('BfcacheReloader', () => {
  let reloadSpy: Mock<() => void>;

  // Constructed once: the reloader registers a `pageshow` listener on
  // `window` for the lifetime of the page, so we route it through an
  // indirection that always calls the *current* test's spy instead of
  // creating (and leaking) a new listener per test.
  beforeAll(() => {
    new BfcacheReloader(() => reloadSpy());
  });

  beforeEach(() => {
    reloadSpy = vi.fn();
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('reloads when the page is restored from bfcache with a pending hx-trigger="load" element', () => {
    document.body.innerHTML = '<div hx-trigger="load"></div>';

    dispatchPageShow(true);

    expect(reloadSpy).toHaveBeenCalledOnce();
  });

  it('does not reload when the page is restored from bfcache without pending load-triggered elements', () => {
    document.body.innerHTML = '<div>Already loaded content</div>';

    dispatchPageShow(true);

    expect(reloadSpy).not.toHaveBeenCalled();
  });

  it('does not reload on a regular (non-persisted) pageshow', () => {
    document.body.innerHTML = '<div hx-trigger="load"></div>';

    dispatchPageShow(false);

    expect(reloadSpy).not.toHaveBeenCalled();
  });
});
