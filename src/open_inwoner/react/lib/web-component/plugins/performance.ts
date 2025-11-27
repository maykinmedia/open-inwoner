import type { WebComponentPlugin } from '../types';

/**
 * Performance monitoring plugin
 * Tracks loading performance of web components
 */
export const performancePlugin: WebComponentPlugin = {
  name: 'performance',

  beforeLoad: async ({ componentName, element }) => {
    const startMark = `wc-${componentName}-start`;
    performance.mark(startMark);
    element.setAttribute('data-load-start', startMark);
    console.log(
      `[Plugin:performance] Start loading component: ${componentName}`
    );
  },

  afterLoad: async ({ componentName, element }) => {
    const startMark = element.getAttribute('data-load-start');
    if (startMark) {
      const endMark = `wc-${componentName}-end`;
      performance.mark(endMark);
      performance.measure(`wc-${componentName}-load`, startMark, endMark);

      const measure = performance.getEntriesByName(
        `wc-${componentName}-load`
      )[0];
      if (measure) {
        console.log(
          `[Plugin:performance] ${componentName} loaded in ${measure.duration.toFixed(2)}ms`
        );
      }

      element.removeAttribute('data-load-start');
    }
  },
};
