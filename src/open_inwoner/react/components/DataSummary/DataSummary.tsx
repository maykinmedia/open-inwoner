import {
  DescriptionList,
  DescriptionListProps,
} from '@gemeente-denhaag/descriptionlist';
import { usePropsOrScriptData } from '@react/lib/json';
import { AnyComponent as AC } from 'preact';
import { formatDate } from '@react/lib/format/format';
import { isDate } from '@react/lib/compare';

export interface ListItem {
  label: string;
  value?: string | number | null;
}

export interface IDataSummaryProps {
  items?: ListItem[];
  itemsId?: string;
}

const DataSummary: AC<IDataSummaryProps> = ({ items, itemsId }) => {
  const data = usePropsOrScriptData<ListItem[]>(items, itemsId);

  if (!data?.length) return <></>;

  const listItems = data.map(({ label, value }) => ({
    title: label,
    detail: isDate(value) ? formatDate(value) : (value ?? '-'),
  })) satisfies DescriptionListProps['items'];

  return <DescriptionList items={listItems} />;
};

export default DataSummary;
