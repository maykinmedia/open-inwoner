import type { WebComponentPlugin } from '../types';

/**
 * Skeleton/FOUCE prevention plugin
 * Adds loading classes to prevent FOUCE
 *
 * @example
 * Usage in CSS:
 * ```scss
 * .wc-loading {
 * /// Some loading effect
 * }
 * .wc-loaded {
 * /// Some loaded effect
 * }
 * .wc-error {
 * /// Some error effect
 * }
 * ```
 */
export const skeletonPlugin: WebComponentPlugin = {
  name: 'skeleton',

  beforeLoad: async ({ element }) => {
    element.classList.add('wc-loading');
    element.setAttribute('aria-busy', 'true');
  },

  afterLoad: async ({ element }) => {
    element.classList.remove('wc-loading');
    element.classList.add('wc-loaded');
    element.removeAttribute('aria-busy');
  },

  onError: ({ element }) => {
    element.classList.remove('wc-loading');
    element.classList.add('wc-error');
    element.removeAttribute('aria-busy');
  },
};
