import { AnyComponent as AC } from 'preact';

export interface ITableRowProps {
  children?: any;
}

const TableRow: AC<ITableRowProps> = ({ children }) => {
  return <tr class="utrecht-table__row">{children}</tr>;
};

export default TableRow;
