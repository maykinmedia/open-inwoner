import {
  DescriptionList,
  DescriptionListProps,
} from '@gemeente-denhaag/descriptionlist';
import { usePropsOrScriptData } from '@react/lib/json';
import { AnyComponent as AC } from 'preact';

export interface ListItem {
  label: string;
  value?: string | number | null;
  type?: 'date';
}

export interface IDataSummaryProps {
  items?: ListItem[];
  itemsId?: string;
}

const formatDate = (value: string) =>
  new Intl.DateTimeFormat(document.documentElement.lang || 'nl-NL', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    timeZone: 'Europe/Amsterdam',
  }).format(new Date(value));

const DataSummary: AC<IDataSummaryProps> = ({ items, itemsId }) => {
  const data = usePropsOrScriptData<ListItem[]>(items, itemsId);

  if (!data?.length) return <></>;

  const listItems = data.map(({ label, value, type }) => ({
    title: label,
    detail:
      type === 'date' && typeof value === 'string'
        ? formatDate(value)
        : (value ?? '-'),
  })) satisfies DescriptionListProps['items'];

  return <DescriptionList items={listItems} />;
};

export default DataSummary;
