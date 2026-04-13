import { within } from '@testing-library/dom';

/**
 * Waits for a custom element to appear in `container` and be fully upgraded
 * (shadow root attached and Preact rendered inside it).
 *
 * Use this at the start of every `play` function that targets a shadow DOM
 * component, instead of a bare `querySelector`.
 *
 * @example
 * play: async ({ canvasElement, step }) => {
 *   const accordion = await waitForCustomElement(canvasElement, 'oip-accordion');
 *   const canvas = shadowWithin(accordion);
 *   ...
 * }
 */
export async function waitForCustomElement(
  container: Element,
  tagName: string
): Promise<Element> {
  // Wait for the custom element class to be registered.
  await customElements.whenDefined(tagName);

  // Poll until the element is in the DOM and has a shadow root,
  // giving Preact time to complete its initial render cycle.
  return new Promise((resolve, reject) => {
    const deadline = Date.now() + 5000;

    const check = () => {
      const el = container.querySelector(tagName);
      if (el?.shadowRoot) {
        resolve(el);
        return;
      }
      if (Date.now() > deadline) {
        reject(
          new Error(
            `waitForCustomElement: <${tagName}> did not appear with a shadow root within 5s`
          )
        );
        return;
      }
      requestAnimationFrame(check);
    };

    check();
  });
}

/**
 * Returns a `within` scope bound to a custom element's shadow root.
 *
 * Use this in Storybook `play` functions instead of `within(canvasElement)`
 * whenever the component renders inside a shadow root.
 *
 * @example
 * play: async ({ canvasElement }) => {
 *   const accordion = await waitForCustomElement(canvasElement, 'oip-accordion');
 *   const canvas = shadowWithin(accordion);
 *   expect(canvas.getByRole('group')).not.toHaveAttribute('open');
 * }
 */
export function shadowWithin(element: Element) {
  if (!element.shadowRoot) {
    throw new Error(
      `shadowWithin: <${element.tagName.toLowerCase()}> has no shadow root. ` +
        'Ensure the custom element is registered and upgraded before calling this.'
    );
  }
  return within(element.shadowRoot as unknown as HTMLElement);
}
