import { IChartProps } from './Chart';
import { AfvalData } from './types';

export const factoryAfvalData = (): AfvalData => [
  {
    object_id: '10001',
    object_address: 'Kerkstraat 12',
    totaal_gewicht: '1.245',
    containers: [
      {
        identifier: '895468490654',
        type: 'Restafval',
        totaal_gewicht: '720',
        ledigingen: [
          {
            tijdstip_datum: '06-01-2025',
            tijdstip_tijd: '07:35',
            tijdstip_dag: 'maandag',
            gewicht: '47,9',
          },
          {
            tijdstip_datum: '03-02-2025',
            tijdstip_tijd: '08:10',
            tijdstip_dag: 'maandag',
            gewicht: '50,2',
          },
        ],
      },
      {
        identifier: '895468490655',
        type: 'GFT',
        totaal_gewicht: '525',
        ledigingen: [
          {
            tijdstip_datum: '13-01-2025',
            tijdstip_tijd: '07:55',
            tijdstip_dag: 'maandag',
            gewicht: '32,1',
          },
          {
            tijdstip_datum: '10-02-2025',
            tijdstip_tijd: '08:20',
            tijdstip_dag: 'maandag',
            gewicht: '29,8',
          },
        ],
      },
    ],
  },
];

export const factoryChart = (
  overrides: Partial<IChartProps> = {}
): IChartProps => ({
  period: 'month',
  ...overrides,
});
