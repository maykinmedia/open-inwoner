import { WebComponentJSXRegistry } from '@react/lib/web-component';

/**
 * Type declarations for custom web components
 */
declare global {
  namespace preact.JSX {
    interface IntrinsicElements extends WebComponentJSXRegistry {}
  }
}

export {};
