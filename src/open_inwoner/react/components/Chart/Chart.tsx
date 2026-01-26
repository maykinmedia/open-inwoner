import { Chart, registerables } from 'chart.js';
import { useEffect, useRef } from 'preact/hooks';
import './Chart.scss';
import { AfvalData, ChartDataPoint, ChartPeriod } from './types';
import { useChart } from './useChart';
import { AnyComponent as AC } from 'preact';
import { FormattedMessage } from 'react-intl';

Chart.register(...registerables);

export interface IChartProps {
  data?: AfvalData;
  period?: ChartPeriod;
  dataId?: string;
}

const OIPChart: AC<IChartProps> = ({ data, period = 'month', dataId }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<Chart<'bar', ChartDataPoint[]> | null>(null);

  // Generate chart configuration using custom hook
  const config = useChart(data, dataId, period);

  // Create or update chart when config changes
  useEffect(() => {
    if (!config || !canvasRef.current) return;

    if (!chartRef.current) {
      // Create chart if it doesn't exist yet
      chartRef.current = new Chart(canvasRef.current, config);
    } else {
      // Update existing chart
      chartRef.current.data = config.data;
      if (config.options) {
        chartRef.current.options = config.options;
      }
      chartRef.current.update();
    }
  }, [config]);

  // Cleanup on unmount
  useEffect(
    () => () => {
      if (chartRef.current) {
        chartRef.current.destroy();
        chartRef.current = null;
      }
    },
    []
  );

  return (
    <div className="afval-chart__container" aria-hidden="true">
      <canvas ref={canvasRef} className="afval-chart">
        <FormattedMessage
          id="chart.default"
          description="The default message of the chart."
          defaultMessage="De grafiek kan niet worden weergegeven. Zie de tabellen hieronder voor de gegevens."
        >
          {(data) => <p>{data}</p>}
        </FormattedMessage>
      </canvas>
    </div>
  );
};

export default OIPChart;
