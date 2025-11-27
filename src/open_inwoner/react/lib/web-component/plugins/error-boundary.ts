import type { WebComponentPlugin } from '../types';

/**
 * Silent error plugin
 * Hides components that fail to load without showing error messages
 */
export const silentErrorPlugin: WebComponentPlugin = {
  name: 'silent-error',

  onError: ({ element }, error) => {
    if (!error) return;
    element.style.display = 'none';
    element.setAttribute('data-wc-error', error.message);
  },
};
