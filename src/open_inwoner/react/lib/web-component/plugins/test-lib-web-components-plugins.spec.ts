import { describe, expect, it, beforeEach, afterEach, vi } from 'vitest';
import { silentErrorPlugin } from './error-boundary';
import { performancePlugin } from './performance';
import { skeletonPlugin } from './skeleton';
import type { WebComponentContext } from '../types';

describe('Test src react/lib/web-components/plugins folder', () => {
  let mockElement: HTMLElement;
  let mockContext: WebComponentContext;

  beforeEach(() => {
    mockElement = document.createElement('div');
    mockContext = {
      componentName: 'test-component',
      element: mockElement,
    };
  });

  describe('Test error-boundary.ts file', () => {
    describe('silentErrorPlugin', () => {
      it('should have the correct name', () => {
        expect(silentErrorPlugin.name).toBe('silent-error');
      });

      it('should hide element and set error attribute when error occurs', () => {
        const error = new Error('Test error message');

        silentErrorPlugin.onError?.(mockContext, error);

        expect(mockElement.style.display).toBe('none');
        expect(mockElement.getAttribute('data-wc-error')).toBe(
          'Test error message'
        );
      });

      it('should not modify element when no error is provided', () => {
        const initialDisplay = mockElement.style.display;

        silentErrorPlugin.onError?.(mockContext);

        expect(mockElement.style.display).toBe(initialDisplay);
        expect(mockElement.hasAttribute('data-wc-error')).toBe(false);
      });

      it('should handle undefined error gracefully', () => {
        silentErrorPlugin.onError?.(mockContext, undefined);

        expect(mockElement.hasAttribute('data-wc-error')).toBe(false);
      });
    });
  });

  describe('Test performance.ts file', () => {
    describe('performancePlugin', () => {
      let consoleLogSpy: any;
      let performanceMarkSpy: any;
      let performanceMeasureSpy: any;

      beforeEach(() => {
        consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
        performanceMarkSpy = vi.spyOn(performance, 'mark');
        performanceMeasureSpy = vi.spyOn(performance, 'measure');
        vi.spyOn(performance, 'getEntriesByName').mockReturnValue([
          { duration: 123.45 } as PerformanceEntry,
        ]);
      });

      afterEach(() => {
        consoleLogSpy.mockRestore();
        performanceMarkSpy.mockRestore();
        performanceMeasureSpy.mockRestore();
      });

      it('should have the correct name', () => {
        expect(performancePlugin.name).toBe('performance');
      });

      it('should mark start time and log on beforeLoad', async () => {
        await performancePlugin.beforeLoad?.(mockContext);

        expect(performanceMarkSpy).toHaveBeenCalledWith(
          'wc-test-component-start'
        );
        expect(mockElement.getAttribute('data-load-start')).toBe(
          'wc-test-component-start'
        );
        expect(consoleLogSpy).toHaveBeenCalledWith(
          '[Plugin:performance] Start loading component: test-component'
        );
      });

      it('should measure performance and log on afterLoad', async () => {
        mockElement.setAttribute('data-load-start', 'wc-test-component-start');

        await performancePlugin.afterLoad?.(mockContext);

        expect(performanceMarkSpy).toHaveBeenCalledWith(
          'wc-test-component-end'
        );
        expect(performanceMeasureSpy).toHaveBeenCalledWith(
          'wc-test-component-load',
          'wc-test-component-start',
          'wc-test-component-end'
        );
        expect(consoleLogSpy).toHaveBeenCalledWith(
          '[Plugin:performance] test-component loaded in 123.45ms'
        );
        expect(mockElement.hasAttribute('data-load-start')).toBe(false);
      });

      it('should not measure performance if start mark is missing', async () => {
        await performancePlugin.afterLoad?.(mockContext);

        expect(performanceMeasureSpy).not.toHaveBeenCalled();
      });

      it('should handle missing measure entry gracefully', async () => {
        mockElement.setAttribute('data-load-start', 'wc-test-component-start');
        vi.spyOn(performance, 'getEntriesByName').mockReturnValue([]);

        await performancePlugin.afterLoad?.(mockContext);

        expect(performanceMeasureSpy).toHaveBeenCalled();
        expect(mockElement.hasAttribute('data-load-start')).toBe(false);
      });
    });
  });

  describe('Test skeleton.ts file', () => {
    describe('skeletonPlugin', () => {
      it('should have the correct name', () => {
        expect(skeletonPlugin.name).toBe('skeleton');
      });

      it('should add loading class and aria-busy attribute on beforeLoad', async () => {
        await skeletonPlugin.beforeLoad?.(mockContext);

        expect(mockElement.classList.contains('wc-loading')).toBe(true);
        expect(mockElement.getAttribute('aria-busy')).toBe('true');
      });

      it('should remove loading class and add loaded class on afterLoad', async () => {
        mockElement.classList.add('wc-loading');
        mockElement.setAttribute('aria-busy', 'true');

        await skeletonPlugin.afterLoad?.(mockContext);

        expect(mockElement.classList.contains('wc-loading')).toBe(false);
        expect(mockElement.classList.contains('wc-loaded')).toBe(true);
        expect(mockElement.hasAttribute('aria-busy')).toBe(false);
      });

      it('should remove loading class and add error class on onError', () => {
        mockElement.classList.add('wc-loading');
        mockElement.setAttribute('aria-busy', 'true');

        skeletonPlugin.onError?.(mockContext);

        expect(mockElement.classList.contains('wc-loading')).toBe(false);
        expect(mockElement.classList.contains('wc-error')).toBe(true);
        expect(mockElement.hasAttribute('aria-busy')).toBe(false);
      });

      it('should handle full lifecycle correctly', async () => {
        // Start loading
        await skeletonPlugin.beforeLoad?.(mockContext);
        expect(mockElement.classList.contains('wc-loading')).toBe(true);
        expect(mockElement.getAttribute('aria-busy')).toBe('true');

        // Finish loading
        await skeletonPlugin.afterLoad?.(mockContext);
        expect(mockElement.classList.contains('wc-loading')).toBe(false);
        expect(mockElement.classList.contains('wc-loaded')).toBe(true);
        expect(mockElement.hasAttribute('aria-busy')).toBe(false);
      });

      it('should handle error lifecycle correctly', async () => {
        // Start loading
        await skeletonPlugin.beforeLoad?.(mockContext);
        expect(mockElement.classList.contains('wc-loading')).toBe(true);
        expect(mockElement.getAttribute('aria-busy')).toBe('true');

        // Error occurs
        skeletonPlugin.onError?.(mockContext);
        expect(mockElement.classList.contains('wc-loading')).toBe(false);
        expect(mockElement.classList.contains('wc-loaded')).toBe(false);
        expect(mockElement.classList.contains('wc-error')).toBe(true);
        expect(mockElement.hasAttribute('aria-busy')).toBe(false);
      });
    });
  });
});
