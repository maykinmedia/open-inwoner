import { AnyComponent as AC } from 'preact';

export interface IDataSummaryProps {
  label: string;
  value?: string | number | null;
}

const DataSummary: AC<IDataSummaryProps> = ({ label, value }) => {
  return (
    <div class="data-summary">
      <dl class="data-summary__container">
        <div class="data-summary__list">
          <dt class="data-summary__label">{label}</dt>
          <dd class="data-summary__value">{value || '-'}</dd>
        </div>
      </dl>
    </div>
  );
};

export default DataSummary;
