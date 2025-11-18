/**
 * Web Components Entry Point
 * Imports all web components which auto-register via @customElement decorator
 */

import CaseCard from '@webcomponents/components/PluginCaseCard/PluginCaseCard';
import CustomButton from '@webcomponents/components/CustomButton';
import CustomCounter from '@webcomponents/components/CustomCounter';
import { defineCustomElements } from '@utrecht/web-component-library-stencil/loader';

// Export components for external use
defineCustomElements();
export { CaseCard, CustomButton, CustomCounter };
