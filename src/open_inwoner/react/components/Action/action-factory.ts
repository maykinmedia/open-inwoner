import { IActionProps } from './Action';

export const factoryAction = (
  overrides: Partial<IActionProps> = {}
): IActionProps => ({
  actionUrl: 'https://example.com',
  message: 'Er is een nieuwe zaak toegevoegd',
  title: 'Mijn Zaken',
  ...overrides,
});

export const factoryActions = (): IActionProps[] => [
  factoryAction({
    message: 'Er is een nieuwe zaak toegevoegd',
    title: 'Mijn Zaken',
  }),
  factoryAction({
    message: 'Controleer uitkeringen',
    title: 'Mijn Uitkeringen',
  }),
  factoryAction({
    message: 'Stel een nieuwe vraag',
    title: 'Mijn Vragen',
  }),
  factoryAction({
    message: 'Start nieuwe samenwerking',
    title: 'Mijn Samenwerkingen',
  }),
];
