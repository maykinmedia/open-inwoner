/**
 * Web Component Utilities
 *
 * This module exports utilities for creating and managing web components.
 *
 * - i18n
 * - registry
 * - types
 */
export { IntlProviderWrapper } from './IntlProviderWrapper';
export { wcPluginRegistry, wcRegistry } from './registry';
export type { WebComponentPlugin, WebComponentRegistry } from './types';
export { withIntl } from './plugins';
