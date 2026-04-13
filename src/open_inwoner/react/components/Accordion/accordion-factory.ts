import { IAccordionProps } from './Accordion';

export const factoryAccordion = (
  overrides: Partial<IAccordionProps> = {}
): IAccordionProps => ({
  initialOpen: false,
  ...overrides,
});
