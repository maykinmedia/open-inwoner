export const getHost = (element: Element) =>
  (element.getRootNode() as ShadowRoot)?.host ?? null;

export const getOptions = (element: Element) => {
  if (!element) return [];
  return [
    ...getHost(element)?.querySelectorAll<HTMLElement>('oip-select-option'),
  ];
};

export const getOption = (element?: Element, index = 0) => {
  if (!element) return null;

  return getOptions(element)[index];
};

export const focusOption = (el?: HTMLElement) =>
  el?.shadowRoot?.querySelector<HTMLElement>('.oip-select-option')?.focus();

export const bindMoveFocus =
  (element: Element | null) => (direction: 'next' | 'prev') => {
    if (!element) return;

    const options = getOptions(element);
    const focused = options.findIndex((el) => el.matches(':focus-within'));
    const next =
      direction === 'next'
        ? Math.min(focused + 1, options.length - 1)
        : Math.max(focused - 1, 0);
    focusOption(options[next]);
  };
