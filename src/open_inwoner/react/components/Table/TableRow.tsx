import { AnyComponent as AC, ComponentChildren } from 'preact';

export interface ITableRowProps {
  children?: ComponentChildren;
}

const TableRow: AC<ITableRowProps> = ({ children }) => {
  return <tr class="utrecht-table__row">{children}</tr>;
};

export default TableRow;
