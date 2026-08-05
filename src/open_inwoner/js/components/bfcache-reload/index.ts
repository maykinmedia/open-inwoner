/**
 * HTMX elements using `hx-trigger="load"` (e.g. the homepage's "Mijn Zaken"
 * plugin) fire their request on the browser's `load` event. That event does
 * not fire again when a page is restored from the back/forward cache
 * (bfcache) via browser back/forward navigation - only `pageshow` does, with
 * `event.persisted` set to `true`.
 *
 * If the page was cached before its `hx-trigger="load"` request finished
 * (e.g. the user navigated away right after the initial page load), the
 * restored page is stuck showing the loading spinner forever, since HTMX
 * never gets a chance to retry.
 *
 * This does not disable bfcache restores in general - a `[hx-trigger="load"]`
 * element is swapped away by HTMX once its request resolves, so on a normal
 * restore (request already finished before the page was cached) the selector
 * below finds nothing and the cached page is shown instantly, as usual. Only
 * when that element is still present - meaning the page was frozen mid-load -
 * do we force a full reload, trading the instant restore for a fresh `load`
 * event that lets the stuck request run again from scratch.
 */
export class BfcacheReloader {
  constructor(private reload: () => void = () => window.location.reload()) {
    window.addEventListener('pageshow', this.handlePageShow.bind(this));
  }

  private handlePageShow(event: PageTransitionEvent): void {
    if (!event.persisted) return;
    if (document.querySelector('[hx-trigger="load"]')) {
      this.reload();
    }
  }
}
