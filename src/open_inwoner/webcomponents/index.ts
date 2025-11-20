/**
 * Web Components Entry Point
 * Imports all web components which auto-register via @customElement decorator
 */

import CustomButton from '@webcomponents/components/CustomButton';
import CustomCounter from '@webcomponents/components/CustomCounter';
import { defineCustomElements } from '@utrecht/web-component-library-stencil/loader';
import HomepagePluginSection from '@webcomponents/components/Sections/HomepagePluginSection';
import LoadingSpinner from '@webcomponents/components/Spinner/Spinner';
import ZakenPluginContainer from '@webcomponents/components/ZakenPlugin/ZakenPluginContainer';
import ZakenPluginZaakItem from '@webcomponents/components/ZakenPlugin/ZakenPluginZaakItem';

// Export components for external use
defineCustomElements();
export {
  CustomButton,
  CustomCounter,
  HomepagePluginSection,
  LoadingSpinner,
  ZakenPluginContainer,
  ZakenPluginZaakItem,
};
