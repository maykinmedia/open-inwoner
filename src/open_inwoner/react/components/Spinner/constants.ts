import { WebComponentDefinition } from '@react/lib/web-component';
import type { ILoadingSpinnerProps } from './Spinner';

export const LOADING_SPINNER_DEFINITION: WebComponentDefinition<
  'oip-loading-spinner',
  ILoadingSpinnerProps
> = {
  tagName: 'oip-loading-spinner',
  propNames: ['iconName', 'loadingText'],
  options: { shadow: false, i18n: false },
  importer: () => import('./Spinner'),
};
