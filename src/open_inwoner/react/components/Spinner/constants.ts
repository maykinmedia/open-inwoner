/**
 * Loading Spinner constants
 *
 * This component doesn't expose any props to the outside.
 */
import { WebComponentDefinition } from '@react/lib/web-component';

export const LOADING_SPINNER_DEFINITION: WebComponentDefinition<
  'oip-loading-spinner',
  {}
> = {
  tagName: 'oip-loading-spinner',
  propNames: [],
  options: { shadow: false, i18n: false },
  importer: () => import('./Spinner'),
};
