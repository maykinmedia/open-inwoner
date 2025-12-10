import { WebComponentLoader } from '@react/lib/web-component/loader';
import htmx from 'htmx.org';

WebComponentLoader.registerWebComponents();

// Re-register the web components after a HTML swap.
// Inside the swap can be web component which are not yet registered
// This way we force these components to be defined.
htmx.on('htmx:afterSwap', () => {
  WebComponentLoader.registerWebComponents();
});
