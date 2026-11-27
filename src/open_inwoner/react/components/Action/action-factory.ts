import { IActionProps } from './Action';

export const factoryAction = (
  overrides: Partial<IActionProps> = {}
): IActionProps => ({
  actionUrl: 'https://example.com',
  message: 'Documenten nodig voor aanvraag bijzondere bijstand',
  label: 'U moet een document toevoegen',
  status: 'warning',
  ...overrides,
});

export const factoryActions = (): IActionProps[] => [
  factoryAction({
    message: 'Documenten nodig voor aanvraag bijzondere bijstand',
    label: 'U moet een document toevoegen',
    status: 'warning',
  }),
  factoryAction({
    message: 'Samenwerkingen: je moet een actie uitvoeren',
    label: 'Bekijk actie',
    status: 'info',
  }),
  factoryAction({
    message: 'Status van aanvraag parkeervergunning verandert naar afgerond',
    label: 'Afgerond',
    status: 'success',
  }),
  factoryAction({
    message: 'Verleng uw identiteitskaart',
    label: undefined,
  }),
];
