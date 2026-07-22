import { withLoader } from '@react/lib/decorators/storybook';
import type { Meta, StoryObj } from '@storybook/preact';
import OIPChart, { IChartProps } from './Chart';
import { CHART_DEFINITION } from './constants';
import mockData2025 from './fixtures/data-2025.json';
import mockDataRest from './fixtures/data-rest.json';
import mockData from './fixtures/data.json';
import { AfvalData } from './types';

const meta: Meta<IChartProps> = {
  title: 'Components/Chart',
  component: OIPChart,
  parameters: {
    layout: 'padded',
  },
  tags: ['Shadow DOM'],
  argTypes: {
    period: {
      control: 'select',
      options: ['week', 'month', 'year'],
      description: 'Time period for data aggregation',
    },
  },
};

export default meta;

type Story = StoryObj<IChartProps>;

const data = mockData as AfvalData;
const data2025 = mockData2025 as AfvalData;
const dataRest = mockDataRest as AfvalData;

// ============================================
// Period: Year
// ============================================

export const YearPeriod: Story = {
  name: 'Year Period (Multi-year data)',
  args: {
    data,
    period: 'year',
  },
};

export const YearPeriod2025Only: Story = {
  name: 'Year Period (2025 only)',
  args: {
    data: data2025,
    period: 'year',
  },
};

export const YearPeriodRestOnly: Story = {
  name: 'Year Period (Restafval only)',
  args: {
    data: dataRest,
    period: 'year',
  },
};

// ============================================
// Period: Month
// ============================================

export const MonthPeriod: Story = {
  name: 'Month Period (Multi-year data)',
  args: {
    data,
    period: 'month',
  },
};

export const MonthPeriod2025Only: Story = {
  name: 'Month Period (2025 only)',
  args: {
    data: data2025,
    period: 'month',
  },
};

// ============================================
// Period: Week
// ============================================

export const WeekPeriod: Story = {
  name: 'Week Period (Multi-year data)',
  args: {
    data,
    period: 'week',
  },
};

export const WeekPeriod2025Only: Story = {
  name: 'Week Period (2025 only)',
  args: {
    data: data2025,
    period: 'week',
  },
};

// ============================================
// Interactive
// ============================================

export const Interactive: Story = {
  name: 'Interactive (try different periods)',
  args: {
    data,
    period: 'month',
  },
};
export const UnknownContainerType: Story = {
  name: 'With unknown container type',
  args: {
    data: data.map((x) => ({
      ...x,
      containers: [{ ...x.containers[0], type: 'Glas' }, ...x.containers],
    })),
  },
};

// ============================================
// Web Component
// ============================================

export const AsWebComponent: Story = {
  name: 'As Web Component',
  args: {
    data,
    period: 'month',
    dataId: 'chart-web-component-data',
  },
  decorators: [withLoader(CHART_DEFINITION.tagName)],
  render: (args) => (
    <>
      <script type="application/json" id={args.dataId}>
        {JSON.stringify(args.data)}
      </script>
      <oip-chart data-id={args.dataId} period={args.period} />
    </>
  ),
};
