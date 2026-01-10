import { AnyComponent as AC, ComponentChildren } from 'preact';

export interface ITableHeaderCellProps {
  content?: string;
  scope?: 'col' | 'row';
  children?: ComponentChildren;
}

const TableHeaderCell: AC<ITableHeaderCellProps> = ({
  content,
  scope = 'col',
  children,
}) => {
  return (
    <th class="utrecht-table__header-cell" scope={scope}>
      {content || children}
    </th>
  );
};

export default TableHeaderCell;
