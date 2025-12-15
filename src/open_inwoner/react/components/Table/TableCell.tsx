import { AnyComponent as AC } from 'preact';

export interface ITableCellProps {
  colSpan?: number | string;
  content?: string; // not available in NLDS
  children?: any;
}

const TableCell: AC<ITableCellProps> = ({ colSpan, content, children }) => {
  return (
    <td
      class="utrecht-table__cell"
      colSpan={colSpan ? parseInt(String(colSpan), 10) : undefined}
    >
      {content || children}
    </td>
  );
};

export default TableCell;
