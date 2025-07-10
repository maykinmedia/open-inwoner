/**
 * Web Components Entry Point
 * Imports all web components which auto-register via @customElement decorator
 */

import CustomButton from '@webcomponents/components/CustomButton'
import CustomCounter from '@webcomponents/components/CustomCounter'
import { defineCustomElements } from '@utrecht/web-component-library-stencil/loader'

// Export components for external use
defineCustomElements()
export { CustomButton, CustomCounter }
