/**
 * This test suite uses the OLD jest implementation, this be changed to vitest/browser.
 *
 * TODO: implement new test logic.
 */
import '@testing-library/jest-dom';
import './index';
import { afterEach, describe, it, expect } from 'vitest';
import { HtmxSpinnerManager } from './index';

function dispatchHtmxEvent(name: string, target: HTMLElement): void {
  document.dispatchEvent(new CustomEvent(name, { detail: { target } }));
}

function buildDom({
  targetId = 'my-target',
  loadingText,
  loadedText,
  liveRegionId = 'my-live-region',
}: {
  targetId?: string;
  loadingText?: string;
  loadedText?: string;
  liveRegionId?: string;
} = {}) {
  const spinnerAttrs = [
    `data-spinner-for="${targetId}"`,
    `data-spinner-live-region="${liveRegionId}"`,
    loadingText ? `loading-text="${loadingText}"` : '',
    loadedText ? `loaded-text="${loadedText}"` : '',
  ]
    .filter(Boolean)
    .join(' ');

  document.body.innerHTML = `
    <div id="${targetId}">Content</div>
    <div id="${liveRegionId}" aria-live="polite"></div>
    <div class="loader-container loader-container--hide" ${spinnerAttrs}></div>
  `;

  return {
    target: document.getElementById(targetId) as HTMLElement,
    spinner: document.querySelector<HTMLElement>(
      `[data-spinner-for="${targetId}"]`
    )!,
    liveRegion: document.getElementById(liveRegionId) as HTMLElement,
  };
}

describe('HtmxSpinnerManager', () => {
  afterEach(() => {
    document.body.innerHTML = '';
  });

  describe('htmx:beforeRequest', () => {
    it('default loading behavior', () => {
      // Set-up
      const { target, spinner, liveRegion } = buildDom();

      // Validate initial UI
      expect(target).not.toHaveClass('spinner-target--loading');
      expect(spinner).toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe('');

      // Dispatch loading
      dispatchHtmxEvent('htmx:beforeRequest', target);

      // Validate updated UI
      expect(target).toHaveClass('spinner-target--loading');
      expect(spinner).not.toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe(
        HtmxSpinnerManager.defaultLoadingText
      );
    });

    it('with custom loading text', () => {
      // Set-up
      const loadingText = 'Even geduld...';
      const { target, liveRegion, spinner } = buildDom({ loadingText });

      // Validate initial UI
      expect(target).not.toHaveClass('spinner-target--loading');
      expect(liveRegion.textContent).toBe('');
      expect(spinner).toHaveClass('loader-container--hide');

      // Dispatch loading
      dispatchHtmxEvent('htmx:beforeRequest', target);

      // Validate updated UI
      expect(target).toHaveClass('spinner-target--loading');
      expect(spinner).not.toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe(loadingText);
    });

    it('does NOT add spinner-target--loading when the spinner lives inside the target', () => {
      // Set-up
      const { target, liveRegion, spinner } = buildDom();
      target.appendChild(spinner); // move spinner inside target

      // Validate initial UI
      expect(target).not.toHaveClass('spinner-target--loading');
      expect(liveRegion.textContent).toBe('');
      expect(spinner).toHaveClass('loader-container--hide');

      // Dispatch loading
      dispatchHtmxEvent('htmx:beforeRequest', target);

      // Validate updated UI
      expect(target).not.toHaveClass('spinner-target--loading');
      expect(spinner).not.toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe(
        HtmxSpinnerManager.defaultLoadingText
      );
    });
  });

  describe('htmx:afterSwap', () => {
    it('default loaded behavior', () => {
      // Set-up
      const { target, spinner, liveRegion } = buildDom();

      // Validate initial UI
      expect(target).not.toHaveClass('spinner-target--loading');
      expect(spinner).toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe('');

      // Dispatch loading
      dispatchHtmxEvent('htmx:beforeRequest', target);

      // Validate updated UI
      expect(target).toHaveClass('spinner-target--loading');
      expect(spinner).not.toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe(
        HtmxSpinnerManager.defaultLoadingText
      );

      // Dispatch loaded
      dispatchHtmxEvent('htmx:afterSwap', target);

      // Validate updated UI
      expect(target).not.toHaveClass('spinner-target--loading');
      expect(spinner).toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe(HtmxSpinnerManager.defaultLoadedText);
    });

    it('with custom loaded text', () => {
      // Set-up
      const loadedText = 'Klaar!';
      const { target, spinner, liveRegion } = buildDom({ loadedText });

      // Validate initial UI
      expect(target).not.toHaveClass('spinner-target--loading');
      expect(spinner).toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe('');

      // Dispatch loading
      dispatchHtmxEvent('htmx:beforeRequest', target);

      // Validate updated UI
      expect(target).toHaveClass('spinner-target--loading');
      expect(spinner).not.toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe(
        HtmxSpinnerManager.defaultLoadingText
      );

      // Dispatch loaded
      dispatchHtmxEvent('htmx:afterSwap', target);

      // Validate updated UI
      expect(target).not.toHaveClass('spinner-target--loading');
      expect(spinner).toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe(loadedText);
    });

    it('still updates the spinner and live region when the spinner was removed from the DOM during the swap', () => {
      // Set-up
      const { target, spinner, liveRegion } = buildDom();

      // Validate initial UI
      expect(target).not.toHaveClass('spinner-target--loading');
      expect(liveRegion.textContent).toBe('');
      expect(spinner).toHaveClass('loader-container--hide');

      // Dispatch loading
      dispatchHtmxEvent('htmx:beforeRequest', target);

      // Validate updated UI
      expect(target).toHaveClass('spinner-target--loading');
      expect(spinner).not.toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe(
        HtmxSpinnerManager.defaultLoadingText
      );

      // Simulate the spinner being swapped away (removed from DOM).
      spinner.remove();

      // Validate updated UI
      expect(spinner).not.toBeInTheDocument();

      // Dispatch loaded - uses cached references, not live DOM queries.
      dispatchHtmxEvent('htmx:afterSwap', target);

      // Validate updated UI
      expect(target).not.toHaveClass('spinner-target--loading');
      expect(spinner).toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe(HtmxSpinnerManager.defaultLoadedText);
    });

    it('does nothing when there is no matching cache entry', () => {
      // Set-up
      const { target, spinner, liveRegion } = buildDom();

      // Validate initial UI
      expect(target).not.toHaveClass('spinner-target--loading');
      expect(spinner).toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe('');

      // No beforeRequest fired - cache is empty.
      dispatchHtmxEvent('htmx:afterSwap', target);

      // Validate updated UI
      expect(target).not.toHaveClass('spinner-target--loading');
      expect(spinner).toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe('');
    });
  });

  describe('htmx:responseError', () => {
    it('default error behavior', () => {
      // Set-up
      const { target, spinner, liveRegion } = buildDom();

      // Validate initial UI
      expect(target).not.toHaveClass('spinner-target--loading');
      expect(spinner).toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe('');
      expect(document.getElementById('any-error')).not.toBeInTheDocument();

      // Dispatch loading
      dispatchHtmxEvent('htmx:beforeRequest', target);

      // Validate updated UI
      expect(target).toHaveClass('spinner-target--loading');
      expect(spinner).not.toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe(
        HtmxSpinnerManager.defaultLoadingText
      );

      // Dispatch error
      dispatchHtmxEvent('htmx:responseError', target);

      // Validate updated UI
      expect(target).toHaveClass('spinner-target--loading');
      expect(spinner).toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe(HtmxSpinnerManager.defaultErrorText);
      expect(document.getElementById('any-error')).not.toBeInTheDocument();
    });

    it('updates #any-error textContent with the default error text', () => {
      // Set-up
      const { target, spinner, liveRegion } = buildDom();
      document.body.insertAdjacentHTML(
        'beforeend',
        '<div id="any-error"></div>'
      );

      // Validate initial UI
      expect(target).not.toHaveClass('spinner-target--loading');
      expect(spinner).toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe('');
      expect(document.getElementById('any-error')?.textContent).toBe('');

      // Dispatch loading
      dispatchHtmxEvent('htmx:beforeRequest', target);

      // Validate updated UI
      expect(target).toHaveClass('spinner-target--loading');
      expect(spinner).not.toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe(
        HtmxSpinnerManager.defaultLoadingText
      );
      expect(document.getElementById('any-error')?.textContent).toBe('');

      // Dispatch error
      dispatchHtmxEvent('htmx:responseError', target);

      // Validate updated UI
      expect(target).toHaveClass('spinner-target--loading');
      expect(spinner).toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe(HtmxSpinnerManager.defaultErrorText);
      expect(document.getElementById('any-error')?.textContent).toBe(
        HtmxSpinnerManager.defaultErrorText
      );
    });

    it('uses the data-error-message attribute from #any-error for both the element and the live region', () => {
      // Set-up
      const { target, spinner, liveRegion } = buildDom();
      const customMessage = 'Aangepaste foutmelding.';
      document.body.insertAdjacentHTML(
        'beforeend',
        `<div id="any-error" data-error-message="${customMessage}"></div>`
      );

      // Validate initial UI
      expect(target).not.toHaveClass('spinner-target--loading');
      expect(spinner).toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe('');
      expect(document.getElementById('any-error')!.textContent).toBe('');

      // Dispatch loading
      dispatchHtmxEvent('htmx:beforeRequest', target);

      // Validate updated UI
      expect(target).toHaveClass('spinner-target--loading');
      expect(spinner).not.toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe(
        HtmxSpinnerManager.defaultLoadingText
      );
      expect(document.getElementById('any-error')!.textContent).toBe('');

      // Dispatch error
      dispatchHtmxEvent('htmx:responseError', target);

      // Validate updated UI
      expect(target).toHaveClass('spinner-target--loading');
      expect(spinner).toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe(customMessage);
      expect(document.getElementById('any-error')?.textContent).toBe(
        customMessage
      );
    });

    it('does nothing when there is no matching cache entry', () => {
      // Set-up
      const { target, liveRegion, spinner } = buildDom();

      // Validate initial UI
      expect(target).not.toHaveClass('spinner-target--loading');
      expect(spinner).toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe('');
      expect(document.getElementById('any-error')).not.toBeInTheDocument();

      // No beforeRequest fired - cache is empty.
      dispatchHtmxEvent('htmx:responseError', target);

      // Validate updated UI
      expect(target).not.toHaveClass('spinner-target--loading');
      expect(spinner).toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe('');
      expect(document.getElementById('any-error')).not.toBeInTheDocument();
    });
  });

  describe('full lifecycle', () => {
    it('initial → loading → loaded (happy flow)', () => {
      const { target, spinner, liveRegion } = buildDom();

      // Initial - nothing has happened yet.
      expect(target).not.toHaveClass('spinner-target--loading');
      expect(spinner).toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe('');

      // Dispatch loading - request starts.
      dispatchHtmxEvent('htmx:beforeRequest', target);

      expect(target).toHaveClass('spinner-target--loading');
      expect(spinner).not.toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe(
        HtmxSpinnerManager.defaultLoadingText
      );

      // Dispatch loaded - swap completes.
      dispatchHtmxEvent('htmx:afterSwap', target);

      // Validate updated UI
      expect(target).not.toHaveClass('spinner-target--loading');
      expect(spinner).toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe(HtmxSpinnerManager.defaultLoadedText);
    });

    it('initial → loading → error', () => {
      // Set-up
      const { target, spinner, liveRegion } = buildDom();
      document.body.insertAdjacentHTML('beforeend', '<div id="any-error"/>');

      // Validate initial UI
      expect(target).not.toHaveClass('spinner-target--loading');
      expect(spinner).toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe('');
      expect(document.getElementById('any-error')?.textContent).toBe('');

      // Dispatch loading
      dispatchHtmxEvent('htmx:beforeRequest', target);

      // Validate updated UI
      expect(target).toHaveClass('spinner-target--loading');
      expect(spinner).not.toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe(
        HtmxSpinnerManager.defaultLoadingText
      );
      expect(document.getElementById('any-error')?.textContent).toBe('');

      // Dispatch error
      dispatchHtmxEvent('htmx:responseError', target);

      // Validate updated UI
      expect(target).toHaveClass('spinner-target--loading');
      expect(spinner).toHaveClass('loader-container--hide');
      expect(liveRegion.textContent).toBe(HtmxSpinnerManager.defaultErrorText);
      expect(document.getElementById('any-error')?.textContent).toBe(
        HtmxSpinnerManager.defaultErrorText
      );
    });
  });
});
