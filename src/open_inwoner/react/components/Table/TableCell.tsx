import { AnyComponent as AC } from 'preact';

export interface ITableCellProps {
  content?: string;
  children?: any;
}

// Role "cell" is set via ElementInternals in web component registration
const TableCell: AC<ITableCellProps> = ({ content, children }) => {
  return <>{content || children}</>;
};

export default TableCell;
