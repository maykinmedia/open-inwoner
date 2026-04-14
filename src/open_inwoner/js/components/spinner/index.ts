/**
 * Handles show/hide and live region announcements for HTMX spinners.
 * Spinners declare their associated target via data-spinner-for="<target-id>".
 *
 * Live region text is read from the spinner element's attributes:
 *   loading-text  — announced when the request starts (default: "Laden...")
 *   loaded-text   — announced when the swap completes (default: "Geladen.")
 *
 * Listeners are registered at module level (not inside DOMContentLoaded) so
 * they fire before HTMX processes hx-trigger="load" elements — which happens
 * inside HTMX's own DOMContentLoaded handler.
 *
 * Properties are cached on htmx:beforeRequest so they remain available in
 * htmx:afterSwap even if the spinner element was removed from the DOM during
 * the swap (e.g. when the spinner lives inside the swap target).
 */

import { HtmxResponseInfo } from 'htmx.org';

interface SpinnerContext {
  spinners: HTMLElement[];
  liveRegions: HTMLElement[];
  loadingText: string;
  loadedText: string;
}

export class HtmxSpinnerManager {
  private spinnerContextCache = new Map<string, SpinnerContext>();

  static defaultLoadingText = 'Laden...';
  static defaultLoadedText = 'Geladen.';
  static defaultErrorText =
    'Er is iets misgegaan bij het ophalen van de data. Ververs de pagina of probeer het later opnieuw.';

  constructor() {
    document.addEventListener(
      'htmx:beforeRequest',
      this.handleBeforeRequest.bind(this)
    );
    document.addEventListener(
      'htmx:afterSwap',
      this.handleAfterSwap.bind(this)
    );
    document.addEventListener(
      'htmx:responseError',
      this.handleResponseError.bind(this)
    );
  }

  private getSpinners(targetId: string) {
    return [
      ...document.querySelectorAll<HTMLElement>(
        `[data-spinner-for="${targetId}"]`
      ),
    ];
  }

  private getLiveRegion(spinner: HTMLElement) {
    const regionId = spinner.dataset.spinnerLiveRegion;
    return regionId ? document.getElementById(regionId) : null;
  }

  private getSpinnerText(
    spinners: HTMLElement[],
    attr: 'loading-text' | 'loaded-text',
    fallback: string
  ) {
    return spinners[0]?.getAttribute(attr) ?? fallback;
  }

  private handleBeforeRequest(e: Event): void {
    const { detail } = e as CustomEvent<HtmxResponseInfo>;
    if (!detail) return;

    const targetId = detail.target?.id;
    if (!targetId) return;

    const spinners = this.getSpinners(targetId);
    const liveRegions = spinners
      .map((s) => this.getLiveRegion(s))
      .filter((r): r is HTMLElement => r !== null);

    const loadingText = this.getSpinnerText(
      spinners,
      'loading-text',
      HtmxSpinnerManager.defaultLoadingText
    );
    const loadedText = this.getSpinnerText(
      spinners,
      'loaded-text',
      HtmxSpinnerManager.defaultLoadedText
    );

    // Cache before the swap - spinner may be removed from DOM during swap.
    this.spinnerContextCache.set(targetId, {
      spinners,
      liveRegions,
      loadingText,
      loadedText,
    });

    // Hide container (spinner is visible).
    spinners.forEach((spinner) =>
      spinner.classList.remove('loader-container--hide')
    );

    // Announce that loading started (Accessibility)
    liveRegions.forEach((region) => (region.textContent = loadingText));

    // Hide the target content only when the spinner is outside it.
    // When the spinner lives inside or is the target, hiding the target
    // would also hide the spinner itself.
    const hasExternalSpinner = spinners.some((s) => !detail.target.contains(s));
    if (hasExternalSpinner)
      detail.target.classList.add('spinner-target--loading');
  }

  private handleAfterSwap(e: Event): void {
    const { detail } = e as CustomEvent<HtmxResponseInfo>;
    if (!detail) return;

    const targetId = detail.target?.id;
    if (!targetId) return;

    const cached = this.spinnerContextCache.get(targetId);
    if (!cached) return;

    const spinners = cached.spinners ?? this.getSpinners(targetId);

    const liveRegions =
      cached.liveRegions ??
      spinners.map((s) => this.getLiveRegion(s)).filter((r) => r !== null);
    const loadedText =
      cached.loadedText ??
      this.getSpinnerText(
        spinners,
        'loaded-text',
        HtmxSpinnerManager.defaultLoadedText
      );

    // Hide spinners (if spinner is not swapped).
    spinners.forEach((spinner) =>
      spinner.classList.add('loader-container--hide')
    );

    // Announce that loading is done (Accessibility)
    liveRegions.forEach((region) => (region.textContent = loadedText));

    detail.target.classList.remove('spinner-target--loading');

    this.spinnerContextCache.delete(targetId);
  }

  private handleResponseError(e: Event): void {
    const { detail } = e as CustomEvent<HtmxResponseInfo>;
    if (!detail) return;

    const targetId = detail.target?.id;
    if (!targetId) return;

    const cached = this.spinnerContextCache.get(targetId);
    if (!cached) return;

    const spinners = cached.spinners ?? this.getSpinners(targetId);
    const liveRegions =
      cached.liveRegions ??
      spinners.map((s) => this.getLiveRegion(s)).filter((r) => r !== null);

    // Hide spinners (error occured).
    spinners.forEach((spinner) =>
      spinner.classList.add('loader-container--hide')
    );

    // Update error text.
    const anyError = document.getElementById('any-error');
    const errorText =
      anyError?.dataset.errorMessage ?? HtmxSpinnerManager.defaultErrorText;

    if (anyError) {
      anyError.textContent = errorText;
    }

    // Announce the error to screen readers via the live region.
    liveRegions.forEach((region) => (region.textContent = errorText));

    this.spinnerContextCache.delete(targetId);
  }
}

new HtmxSpinnerManager();
